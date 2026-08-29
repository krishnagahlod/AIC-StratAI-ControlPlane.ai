def compute(performance: float, cost: float, responsibility: float, w_perf: float, w_cost: float, w_resp: float) -> float:
    total_weight = w_perf + w_cost + w_resp
    if total_weight <= 0:
        w_perf, w_cost, w_resp, total_weight = 1, 1, 1, 3
    score = (performance * w_perf + cost * w_cost + responsibility * w_resp) / total_weight
    return round(max(0.0, min(100.0, score)), 1)


def risk_level_for(trust_score: float) -> str:
    if trust_score >= 90:
        return "minimal"
    if trust_score >= 70:
        return "low"
    if trust_score >= 30:
        return "moderate"
    return "critical"
