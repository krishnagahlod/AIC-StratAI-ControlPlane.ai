import logging
import re
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import App, Interaction
from app.db.session import get_db
from app.evaluation.orchestrator import evaluate_interaction
from app.proxy import sync_checks
from app.proxy.llm_client import LLMUnavailableError, generate_chat

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("controlplane.proxy")


class ChatMessage(BaseModel):
    role: str
    content: str


class RequestMetadata(BaseModel):
    app_key: str
    task_type: str = "general"


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    metadata: RequestMetadata | None = None
    rag_context: str | None = None


def _resolve_app(db: Session, metadata: RequestMetadata | None) -> App:
    if metadata:
        app = db.query(App).filter(App.key == metadata.app_key).first()
        if app:
            return app
    fallback = db.query(App).order_by(App.id).first()
    if fallback is None:
        raise HTTPException(status_code=400, detail="No apps registered. Run the seed script first.")
    return fallback


def _friendly_llm_error(exc: Exception) -> str:
    """Turn a provider exception into something a human can act on.

    The raw google-genai error is a multi-line JSON blob with quota metadata and help
    links. Surfacing that verbatim in the UI is unreadable, and on a recorded demo it
    looks like a crash rather than a rate limit.
    """
    text = str(exc)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        retry = re.search(r"retry in ([\d.]+)s", text, re.I) or re.search(r"'retryDelay': '(\d+)s'", text)
        wait = f" Retry in about {int(float(retry.group(1)))}s." if retry else ""
        return (
            "The upstream model provider has hit its request quota for every configured "
            f"model tier.{wait} The evaluation pipeline is unaffected — only new live calls are blocked."
        )
    if "API key" in text or "API_KEY" in text or "PERMISSION_DENIED" in text:
        return "The upstream model rejected our API key. Check GEMINI_API_KEY in backend/.env and restart the backend."
    return "The upstream model provider is temporarily unavailable. Please retry shortly."


def _generate_with_fallback(messages: list[dict], model: str, system_prompt: str | None):
    """Try the requested model, then the cheaper judge tier, before giving up.

    Free-tier Gemini quotas are per-model *per day*, so a single exhausted model would
    otherwise take the whole proxy down even while another tier still has headroom.
    Returns the result and the model that actually served it, so the trace records what
    was really called rather than what was asked for.
    """
    candidates = [model]
    judge = settings.gemini_judge_model
    if judge and judge not in candidates:
        candidates.append(judge)

    last_exc: Exception | None = None
    for candidate in candidates:
        try:
            return generate_chat(messages, model=candidate, system_prompt=system_prompt), candidate
        except LLMUnavailableError as exc:
            logger.warning("Model %s unavailable, trying next tier: %s", candidate, exc)
            last_exc = exc

    raise HTTPException(status_code=503, detail=_friendly_llm_error(last_exc))


def _block_message(reason: str) -> str:
    return f"Request blocked by ControlPlane.ai: {reason}"


def _blocked_response(request_id: str, model: str, reason: str, interaction: Interaction) -> dict:
    # A blocked request still carries the `controlplane` envelope. Callers use it to
    # correlate the block with its trace, and omitting it made a blocked prompt
    # indistinguishable from a transport failure on the client side.
    return {
        "id": request_id,
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": _block_message(reason)},
                "finish_reason": "content_filter",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "controlplane": {
            "interaction_id": interaction.id,
            "sync_action": interaction.sync_action,
            "sync_flags": interaction.sync_flags,
            "latency_ms": 0.0,
            "model_called": False,
            "block_reason": reason,
        },
    }


@router.post("/v1/chat/completions")
def chat_completions(payload: ChatCompletionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    request_id = f"cpai-{uuid.uuid4().hex[:12]}"
    app = _resolve_app(db, payload.metadata)
    model = payload.model or settings.gemini_model
    task_type = payload.metadata.task_type if payload.metadata else "general"

    user_messages = [m for m in payload.messages if m.role != "system"]
    system_messages = [m.content for m in payload.messages if m.role == "system"]
    # The application's own configured operating instruction is the base. A caller-supplied
    # system message layers on top of it rather than replacing it — an app's guardrails
    # should not be removable by the request that the guardrails exist to constrain.
    layers = [app.system_prompt] if app.system_prompt else []
    layers.extend(system_messages)
    system_prompt = "\n\n".join(layers) or None
    original_prompt = user_messages[-1].content if user_messages else ""

    if payload.rag_context:
        grounding_instruction = (
            "Answer using ONLY the following source context. If the context does not contain "
            "the answer, say you don't have that information rather than guessing.\n\n"
            f"Source context:\n{payload.rag_context}"
        )
        system_prompt = f"{system_prompt}\n\n{grounding_instruction}" if system_prompt else grounding_instruction

    if sync_checks.budget_tracker.is_over_budget(app.id, app.daily_budget_usd):
        interaction = Interaction(
            app_id=app.id,
            task_type=task_type,
            prompt=original_prompt,
            system_prompt=system_prompt,
            rag_context=payload.rag_context,
            raw_response="",
            # The caller is told why it was blocked, so the trace must record the same
            # thing — an empty delivered_response reads as "nothing happened" in the UI.
            delivered_response=_block_message("daily AI budget for this app has been exceeded"),
            model=model,
            sync_action="blocked",
            sync_flags=[{"type": "budget_exceeded"}],
            source="live",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        background_tasks.add_task(evaluate_interaction, interaction.id)
        return _blocked_response(
            request_id, model, "daily AI budget for this app has been exceeded", interaction
        )

    prompt_check = sync_checks.check_prompt(original_prompt)
    if prompt_check.action == "blocked":
        interaction = Interaction(
            app_id=app.id,
            task_type=task_type,
            prompt=original_prompt,
            system_prompt=system_prompt,
            rag_context=payload.rag_context,
            raw_response="",
            delivered_response=_block_message("prompt matched a blocked jailbreak/injection pattern"),
            model=model,
            sync_action="blocked",
            sync_flags=prompt_check.flags,
            source="live",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        # Blocked interactions are evaluated too: the block itself is a governance event
        # that belongs in the trace, the scores, and the audit trail.
        background_tasks.add_task(evaluate_interaction, interaction.id)
        return _blocked_response(
            request_id, model, "prompt matched a blocked jailbreak/injection pattern", interaction
        )

    sanitized_messages = [m.model_dump() for m in user_messages[:-1]] + [{"role": "user", "content": prompt_check.text}]

    llm_result, model = _generate_with_fallback(sanitized_messages, model, system_prompt)

    response_check = sync_checks.check_response(llm_result.text)

    interaction = Interaction(
        app_id=app.id,
        task_type=task_type,
        prompt=original_prompt,
        system_prompt=system_prompt,
        rag_context=payload.rag_context,
        raw_response=llm_result.text,
        delivered_response=response_check.text,
        model=model,
        input_tokens=llm_result.input_tokens,
        output_tokens=llm_result.output_tokens,
        latency_ms=llm_result.latency_ms,
        sync_action=response_check.action if response_check.action != "allowed" else prompt_check.action,
        sync_flags=prompt_check.flags + response_check.flags,
        source="live",
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    background_tasks.add_task(evaluate_interaction, interaction.id)

    return {
        "id": request_id,
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_check.text},
                "finish_reason": "content_filter" if response_check.action == "blocked" else "stop",
            }
        ],
        "usage": {
            "prompt_tokens": llm_result.input_tokens,
            "completion_tokens": llm_result.output_tokens,
            "total_tokens": llm_result.input_tokens + llm_result.output_tokens,
        },
        "controlplane": {
            "interaction_id": interaction.id,
            "sync_action": interaction.sync_action,
            "sync_flags": interaction.sync_flags,
            "latency_ms": round(llm_result.latency_ms, 1),
            "model_called": True,
            "prompt_check_action": prompt_check.action,
            "response_check_action": response_check.action,
        },
    }
