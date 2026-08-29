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

    start = time.perf_counter()
    try:
        response = _client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=final_system) if final_system else None,
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
    model = model or settings.gemini_judge_model
    try:
        response = _client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini judge call failed, degrading to no-signal: %s", exc)
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
