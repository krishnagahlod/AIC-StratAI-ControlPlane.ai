import json
import logging
import re
import time
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.config import get_settings

settings = get_settings()
_client = genai.Client(api_key=settings.gemini_api_key)
logger = logging.getLogger("controlplane.llm")


class LLMUnavailableError(RuntimeError):
    pass


def model_chain(primary: str | None = None) -> list[str]:
    """Ordered, de-duplicated list of models to try for a single logical call.

    Quota on the free tier is per model, per project, per day — so an exhausted model
    is a routine condition, not an outage. Walking a ladder keeps the pipeline running
    on whichever tier still has headroom instead of failing the request.
    """
    chain = [primary or settings.gemini_model, settings.gemini_judge_model]
    chain += [m.strip() for m in settings.gemini_fallback_models.split(",") if m.strip()]
    seen, out = set(), []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


def _messages_to_contents(messages: list[dict]) -> tuple[str | None, list[types.Content]]:
    system_prompt = None
    contents: list[types.Content] = []
    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            system_prompt = (system_prompt + "\n" if system_prompt else "") + msg["content"]
            continue
        contents.append(
            types.Content(
                role="model" if role == "assistant" else "user",
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )
    return system_prompt, contents


def generate_chat(
    messages: list[dict],
    model: str | None = None,
    system_prompt: str | None = None,
) -> LLMResult:
    model = model or settings.gemini_model
    inferred_system, contents = _messages_to_contents(messages)
    final_system = system_prompt or inferred_system

    def _config(with_thinking: bool):
        kwargs = dict(
            system_instruction=final_system,
            # Backstop only — brevity is enforced by each app's system prompt. Set
            # generously so it never truncates a well-behaved answer mid-sentence.
            max_output_tokens=800,
            temperature=0.4,
        )
        if with_thinking:
            # Models that reason before answering add ~10s to a short grounded reply,
            # which buys nothing here and spends the app's latency budget.
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        return types.GenerateContentConfig(**kwargs)

    start = time.perf_counter()
    try:
        try:
            response = _client.models.generate_content(
                model=model, contents=contents, config=_config(True)
            )
        except Exception as exc:  # noqa: BLE001
            # Not every model accepts an explicit thinking budget; the newer tiers reject
            # it with a 400. That is a config incompatibility, not an outage, so drop the
            # hint and retry rather than burning a fallback hop on it.
            if "INVALID_ARGUMENT" not in str(exc):
                raise
            logger.info("Model %s rejected thinking_config; retrying without it", model)
            response = _client.models.generate_content(
                model=model, contents=contents, config=_config(False)
            )
    except Exception as exc:  # noqa: BLE001 - upstream provider errors are surfaced uniformly
        logger.warning("Gemini generate_chat call failed: %s", exc)
        raise LLMUnavailableError(str(exc)) from exc
    latency_ms = (time.perf_counter() - start) * 1000

    usage = response.usage_metadata
    output_tokens = (getattr(usage, "candidates_token_count", 0) or 0) + (
        getattr(usage, "thoughts_token_count", 0) or 0
    )
    return LLMResult(
        text=response.text or "",
        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def generate_judge_json(prompt: str, model: str | None = None) -> dict:
    """Best-effort LLM-as-judge call. Returns {} on any failure (rate limit, timeout,
    malformed output) so a single flaky judge call degrades to 'no signal from this
    check' rather than losing the whole evaluation pipeline for an interaction."""
    response = None
    for candidate in model_chain(model or settings.gemini_judge_model):
        try:
            response = _client.models.generate_content(
                model=candidate,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Judge model %s unavailable, trying next tier: %s", candidate, exc)
    if response is None:
        logger.warning("All judge model tiers exhausted, degrading to no-signal")
        return {}

    raw = response.text or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}


def generate_text(prompt: str, model: str | None = None, fallback: str = "") -> str:
    model = model or settings.gemini_model
    try:
        response = _client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini generate_text call failed: %s", exc)
        return fallback or "Narrative generation is temporarily unavailable (upstream LLM rate limit or error). Please retry shortly."
    return response.text or ""
