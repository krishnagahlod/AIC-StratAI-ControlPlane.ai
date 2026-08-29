PERFORMANCE_PENALTY_BY_SEVERITY = {"critical": 45, "high": 30, "medium": 15, "low": 5}
RESPONSIBILITY_PENALTY_BY_SEVERITY = {"critical": 50, "high": 30, "medium": 15, "low": 5}
COST_PENALTY_BY_TYPE = {
    "model_overuse": 20,
    "redundant_call": 12,
    "agent_loop_suspected": 45,
    "budget_near_limit": 10,
}


def score_by_severity(flags: list[dict], penalty_by_severity: dict[str, int], base: float = 100.0) -> float:
    score = base
    for flag in flags:
        score -= penalty_by_severity.get(flag["severity"], 10)
    return round(max(0.0, min(100.0, score)), 1)


def score_cost(flags: list[dict], base: float = 100.0) -> float:
    score = base
    for flag in flags:
        score -= COST_PENALTY_BY_TYPE.get(flag["type"], 10)
    return round(max(0.0, min(100.0, score)), 1)
