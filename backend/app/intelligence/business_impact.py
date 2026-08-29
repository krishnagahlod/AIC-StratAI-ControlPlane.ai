from app.config import BUSINESS_ASSUMPTIONS as BA

FLAG_TO_CATEGORY = {
    "hallucination_numeric_mismatch": "revenue",
    "hallucination_llm_judge": "revenue",
    "semantic_contradiction": "revenue",
    "overconfident_wrong": "revenue",
    "incomplete_response": "revenue",
    "incoherent_response": "revenue",
    "pii_leak": "compliance",
    "data_leakage": "compliance",
    "safety_violation": "compliance",
    "bias": "reputation",
    "toxicity": "customer_trust",
    "prompt_injection": "security",
    "model_overuse": "operational_cost",
    "redundant_call": "operational_cost",
    "agent_loop_suspected": "operational_cost",
    "budget_near_limit": "operational_cost",
}

_CATEGORY_PRIORITY = [
    "compliance",
    "customer_trust",
    "security",
    "revenue",
    "reputation",
    "operational_cost",
]


def _pick_lead_flag(flags: list[dict]) -> dict | None:
    if not flags:
        return None
    severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    return max(flags, key=lambda f: (severity_rank.get(f["severity"], 0), _CATEGORY_PRIORITY.index(
        FLAG_TO_CATEGORY.get(f["type"], "operational_cost")
    ) * -1))


def compute(app, flags: list[dict], cost_flags_evidence: dict | None = None) -> dict:
    lead_flag = _pick_lead_flag(flags)
    if lead_flag is None:
        return {
            "risk_category": "none",
            "estimated_impact_usd": 0.0,
            "affected_users": 0,
            "confidence": 0.95,
            "narrative": f"No material issues detected for {app.name}. Response met performance, cost, and responsibility thresholds.",
        }

    category = FLAG_TO_CATEGORY.get(lead_flag["type"], "operational_cost")
    weekly = BA["weekly_interactions_per_app"]
    daily = weekly / 7
    is_customer_facing = app.app_type == "customer_facing"
    confidence = 0.85 if lead_flag["method"] == "deterministic" else 0.65

    if category == "revenue":
        affected_users = round(daily if is_customer_facing else daily * 0.2)
        error_probability = 0.15 if lead_flag["severity"] in ("high", "critical") else 0.05
        impact = affected_users * BA["avg_order_value_usd"] * error_probability
        narrative = (
            f"{app.name} gave a response flagged as '{lead_flag['type']}' "
            f"(severity {lead_flag['severity']}). If representative of a wider pattern, "
            f"this could affect roughly {affected_users:,} users/day, putting an estimated "
            f"${impact:,.0f} in potential refunds, rework, or lost revenue at risk."
        )
    elif category == "compliance":
        affected_users = 1 if not is_customer_facing else round(daily * 0.02)
        impact = (
            BA["gdpr_fine_reference_usd"] * BA["gdpr_fine_probability_per_pii_incident"]
            + BA["remediation_cost_per_compliance_incident_usd"]
        )
        narrative = (
            f"{app.name} triggered a compliance-relevant flag ('{lead_flag['type']}'). "
            f"Even though it was auto-redacted, the expected regulatory exposure "
            f"(probability-weighted GDPR/EU AI Act fine risk plus remediation cost) is "
            f"approximately ${impact:,.0f}."
        )
    elif category == "reputation":
        impact = BA["reputation_incident_base_cost_usd"] * (2 if is_customer_facing else 1)
        affected_users = round(daily * 0.05) if is_customer_facing else 0
        narrative = (
            f"{app.name} produced a response flagged for bias. In a customer- or employee-facing "
            f"context this carries reputational and potential legal exposure estimated at ${impact:,.0f}."
        )
    elif category == "customer_trust":
        affected_users = round(daily)
        impact = affected_users * BA["churn_probability_per_toxicity_incident"] * BA["customer_lifetime_value_usd"]
        narrative = (
            f"{app.name} returned a toxic/harmful response. Extrapolated across its daily traffic "
            f"(~{affected_users:,} interactions), the expected customer-lifetime-value impact from "
            f"elevated churn risk is approximately ${impact:,.0f}."
        )
    elif category == "security":
        affected_users = 0
        impact = BA["remediation_cost_per_compliance_incident_usd"] * 2
        narrative = (
            f"{app.name} was targeted by a suspected prompt injection / jailbreak attempt. "
            f"Estimated incident-response and hardening cost: ${impact:,.0f}."
        )
    else:  # operational_cost
        affected_users = 0
        savings = 0.0
        if cost_flags_evidence:
            savings = cost_flags_evidence.get("potential_savings_usd", 0.0) or 0.0
        impact = max(savings, 0.01) * 30 * 10
        narrative = (
            f"{app.name} shows a cost-efficiency flag ('{lead_flag['type']}'). If this pattern "
            f"repeats across similar calls, projected monthly waste is approximately ${impact:,.0f}."
        )

    return {
        "risk_category": category,
        "estimated_impact_usd": round(impact, 2),
        "affected_users": int(affected_users),
        "confidence": confidence,
        "narrative": narrative,
    }
