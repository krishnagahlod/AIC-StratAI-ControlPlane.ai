import time

from app.config import (
    CHEAP_MODEL_TIER,
    COMPLEX_TASK_KEYWORDS,
    DEFAULT_PRICING,
    EXPENSIVE_MODEL_TIER,
    MID_MODEL_TIER,
    PRICING_TABLE,
    SIMPLE_TASK_KEYWORDS,
)
from app.evaluation.scoring import score_cost
from app.proxy.sync_checks import budget_tracker

_RECENT_WINDOW_SECONDS = 600
_LOOP_WINDOW_SECONDS = 120
_LOOP_THRESHOLD = 5
_recent_prompts: dict[int, list[tuple[str, float]]] = {}


def _normalize(prompt: str) -> str:
    return " ".join(prompt.lower().split())


def _jaccard(a: str, b: str) -> float:
    set_a, set_b = set(a.split()), set(b.split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _classify_complexity(prompt: str) -> str:
    normalized = _normalize(prompt)
    if any(keyword in normalized for keyword in COMPLEX_TASK_KEYWORDS):
        return "complex"
    if len(normalized) <= 60 and any(keyword in normalized for keyword in SIMPLE_TASK_KEYWORDS):
        return "simple"
    if len(normalized) <= 30:
        return "simple"
    return "moderate"


def _model_tier(model: str) -> str:
    if model in CHEAP_MODEL_TIER:
        return "cheap"
    if model in MID_MODEL_TIER:
        return "mid"
    if model in EXPENSIVE_MODEL_TIER:
        return "expensive"
    return "mid"


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING_TABLE.get(model, DEFAULT_PRICING)
    return (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]


_compute_cost = compute_cost


def _check_redundant(app_id: int, prompt: str, now: float) -> bool:
    normalized = _normalize(prompt)
    history = _recent_prompts.setdefault(app_id, [])
    history[:] = [(p, ts) for p, ts in history if now - ts < _RECENT_WINDOW_SECONDS]
    is_redundant = any(_jaccard(normalized, p) > 0.85 for p, _ in history)
    history.append((normalized, now))
    return is_redundant


def _check_agent_loop(app_id: int, now: float) -> bool:
    history = _recent_prompts.get(app_id, [])
    recent_count = sum(1 for _, ts in history if now - ts < _LOOP_WINDOW_SECONDS)
    return recent_count >= _LOOP_THRESHOLD


def analyze(app_id: int, prompt: str, model: str, input_tokens: int, output_tokens: int, daily_budget_usd: float) -> dict:
    now = time.time()
    flags: list[dict] = []

    cost_usd = _compute_cost(model, input_tokens, output_tokens)
    complexity = _classify_complexity(prompt)
    tier = _model_tier(model)

    if complexity == "simple" and tier in ("mid", "expensive"):
        cheap_cost = _compute_cost("gemini-2.5-flash-lite", input_tokens, output_tokens)
        potential_savings = max(cost_usd - cheap_cost, 0.0)
        flags.append(
            {
                "type": "model_overuse",
                "dimension": "cost",
                "severity": "medium",
                "method": "rule_based",
                "detail": f"{model} ({tier} tier) used for a simple/FAQ-style task; a cheaper tier would likely suffice.",
                "evidence": {"potential_savings_usd": round(potential_savings, 5), "complexity": complexity},
            }
        )

    if _check_redundant(app_id, prompt, now):
        flags.append(
            {
                "type": "redundant_call",
                "dimension": "cost",
                "severity": "low",
                "method": "rule_based",
                "detail": "A near-identical prompt was seen recently for this app — a caching layer could avoid this cost.",
            }
        )

    if _check_agent_loop(app_id, now):
        flags.append(
            {
                "type": "agent_loop_suspected",
                "dimension": "cost",
                "severity": "critical",
                "method": "rule_based",
                "detail": f"{_LOOP_THRESHOLD}+ calls from this app within {_LOOP_WINDOW_SECONDS}s — possible reasoning loop or runaway agent.",
            }
        )

    budget_tracker.record(app_id, cost_usd)
    remaining_pct = budget_tracker.budget_remaining_pct(app_id, daily_budget_usd)
    if remaining_pct < 20:
        flags.append(
            {
                "type": "budget_near_limit",
                "dimension": "cost",
                "severity": "medium" if remaining_pct > 0 else "high",
                "method": "rule_based",
                "detail": f"App has {remaining_pct}% of its daily AI budget remaining.",
            }
        )

    score = score_cost(flags)

    return {
        "score": score,
        "flags": flags,
        "cost_usd": round(cost_usd, 6),
        "complexity": complexity,
        "model_tier": tier,
        "daily_spend_usd": round(budget_tracker.spend(app_id), 4),
        "budget_remaining_pct": remaining_pct,
    }
