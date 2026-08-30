import re

from app.evaluation.scoring import PERFORMANCE_PENALTY_BY_SEVERITY, score_by_severity
from app.proxy.llm_client import generate_judge_json

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?\s?%|\$\s?\d+(?:,\d{3})*(?:\.\d+)?|\b\d+(?:,\d{3})*(?:\.\d+)?\b")
_ASSERTIVE_RE = re.compile(
    r"\b(definitely|certainly|guarantee[sd]?|100%|always|without a doubt|absolutely|no question)\b",
    re.IGNORECASE,
)
_HEDGE_RE = re.compile(
    r"\b(might|could|possibly|perhaps|i think|it seems|likely|may|not certain|unsure)\b",
    re.IGNORECASE,
)

JUDGE_PROMPT = """You are a strict AI response auditor checking a chatbot's reply for correctness.

User prompt:
{prompt}

Source/reference context available to the assistant (may be empty if none was provided):
{context}

Assistant's response to audit:
{response}

If the source context is empty, you cannot verify facts — only assess internal plausibility,
completeness, and coherence, and set "verifiable" to false.

Return strict JSON with exactly these fields:
{{
  "verifiable": true/false,
  "faithful_to_context": true/false,
  "hallucination_detected": true/false,
  "fabricated_claims": ["short phrase", ...],
  "contradicts_context": true/false,
  "completeness": 0.0-1.0,
  "coherence": 0.0-1.0,
  "explanation": "one sentence"
}}"""


def _extract_numbers(text: str) -> set[str]:
    return {m.strip() for m in _NUMBER_RE.findall(text)}


def _deterministic_numeric_check(response: str, rag_context: str | None) -> dict | None:
    if not rag_context:
        return None
    context_numbers = _extract_numbers(rag_context)
    response_numbers = _extract_numbers(response)
    if not context_numbers:
        return None
    unmatched = response_numbers - context_numbers
    if not unmatched:
        return None
    return {
        "type": "hallucination_numeric_mismatch",
        "dimension": "performance",
        "severity": "high",
        "method": "deterministic",
        "detail": f"Response cites value(s) {sorted(unmatched)} not present in the provided source context.",
        "evidence": {"response_values": sorted(unmatched), "context_values": sorted(context_numbers)},
    }


def _latency_check(latency_ms: float | None, budget_ms: int | None) -> dict | None:
    """Every app declares a latency budget; this is what makes that declaration mean something.

    Deterministic on purpose — a stopwatch comparison should never be delegated to a model.
    """
    if not latency_ms or not budget_ms or latency_ms <= budget_ms:
        return None
    overrun = latency_ms / budget_ms
    return {
        "type": "latency_budget_exceeded",
        "dimension": "performance",
        "severity": "high" if overrun >= 2 else "medium",
        "method": "deterministic",
        "detail": (
            f"Response took {latency_ms:.0f}ms against this application's "
            f"{budget_ms}ms budget ({overrun:.1f}x over)."
        ),
        "evidence": {"latency_ms": round(latency_ms), "budget_ms": budget_ms, "overrun_x": round(overrun, 2)},
    }


def analyze(
    prompt: str,
    response: str,
    rag_context: str | None,
    latency_ms: float | None = None,
    latency_budget_ms: int | None = None,
) -> dict:
    flags: list[dict] = []

    deterministic_flag = _deterministic_numeric_check(response, rag_context)
    if deterministic_flag:
        flags.append(deterministic_flag)

    latency_flag = _latency_check(latency_ms, latency_budget_ms)
    if latency_flag:
        flags.append(latency_flag)

    judge = generate_judge_json(
        JUDGE_PROMPT.format(prompt=prompt, context=rag_context or "(none provided)", response=response)
    )

    verifiable = bool(judge.get("verifiable", False))
    hallucination = bool(judge.get("hallucination_detected", False))
    contradicts = bool(judge.get("contradicts_context", False))
    completeness = float(judge.get("completeness", 0.8) or 0.8)
    coherence = float(judge.get("coherence", 0.8) or 0.8)

    if hallucination:
        flags.append(
            {
                "type": "hallucination_llm_judge",
                "dimension": "performance",
                "severity": "high" if verifiable else "medium",
                "method": "llm_judge",
                "detail": judge.get("explanation", "LLM-as-judge flagged a likely fabricated claim."),
                "evidence": {
                    "fabricated_claims": judge.get("fabricated_claims", []),
                    "verifiable": verifiable,
                },
            }
        )
    if contradicts:
        flags.append(
            {
                "type": "semantic_contradiction",
                "dimension": "performance",
                "severity": "high",
                "method": "llm_judge",
                "detail": "Response contradicts the provided source/reference context.",
            }
        )
    if completeness < 0.6:
        flags.append(
            {
                "type": "incomplete_response",
                "dimension": "performance",
                "severity": "medium",
                "method": "llm_judge",
                "detail": f"Response only partially addresses the query (completeness={completeness:.2f}).",
            }
        )
    if coherence < 0.6:
        flags.append(
            {
                "type": "incoherent_response",
                "dimension": "performance",
                "severity": "medium",
                "method": "llm_judge",
                "detail": f"Response structure/logic is weak (coherence={coherence:.2f}).",
            }
        )

    has_hallucination_flag = any(f["type"].startswith("hallucination") for f in flags)
    if has_hallucination_flag and _ASSERTIVE_RE.search(response) and not _HEDGE_RE.search(response):
        flags.append(
            {
                "type": "overconfident_wrong",
                "dimension": "performance",
                "severity": "high",
                "method": "deterministic",
                "detail": "Response uses highly assertive language while containing an unverified/fabricated claim.",
            }
        )

    score = score_by_severity(flags, PERFORMANCE_PENALTY_BY_SEVERITY)
    return {"score": score, "flags": flags}
