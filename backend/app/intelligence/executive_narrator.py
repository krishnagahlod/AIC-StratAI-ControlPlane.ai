from app.config import get_settings
from app.intelligence import grounding
from app.proxy.llm_client import generate_text, model_chain

# Each persona asks for a different *register*, never for detail the aggregate
# stats cannot supply. The original engineer instruction asked the model to name
# "affected apps" and "concrete pipeline fixes" while the stats contained neither
# — so it invented both. Specificity is now scoped to what we actually pass in.
AUDIENCE_INSTRUCTIONS = {
    "engineer": (
        "Write for an ML engineer. Be technical and precise, but only about the data below: "
        "name the flag types and their counts, reference the monitored applications by their "
        "exact names as listed, and describe what the scores indicate. If the data does not "
        "explain WHY a flag fired, say that root-cause analysis requires the individual traces "
        "rather than proposing a cause. 3-5 sentences."
    ),
    "ciso": (
        "Write for a CISO/compliance officer. Focus on PII/safety/security incidents, regulatory "
        "exposure (GDPR/EU AI Act framing), auto-redaction vs manual intervention counts, and current "
        "compliance posture as a percentage. 3-5 sentences."
    ),
    "ceo": (
        "Write for a CEO/CTO with no technical background. Lead with the overall TrustScore and trend, "
        "the single biggest business risk in plain dollars, one recommended action with a time estimate, "
        "and total AI spend this period vs budget. 3-5 sentences, no jargon."
    ),
}

PROMPT = """You are ControlPlane.ai's Executive Narrator, generating a plain-English AI health report.

Audience: {audience}
Instructions: {instructions}

Aggregated data for the period:
{stats}

GROUNDING RULES (these override the style instructions above):
- Every number you state must come from the data above.
- Every proper noun must come from the data above. Do NOT invent or guess the names of
  services, microservices, agents, pipelines, modules, endpoints, or internal systems.
  The only application names that exist are the ones listed under monitored_applications.
- Do NOT state a root cause, a reason, or a remediation that is underway unless the data
  above says so. If the data does not explain why something happened, write that the cause
  requires trace-level investigation.
- It is better to say "the data does not show this" than to write a plausible guess.

Write the report now as plain prose (no markdown headers, no bullet lists), in the voice of a
confident but honest internal report.
"""

_CORRECTION = """

Your previous draft was rejected by an automated grounding check because it referenced these
terms, which do not appear anywhere in the data: {terms}.
These are fabrications. Rewrite the report without them, using only names present in the data.
"""

_UNAVAILABLE = "__llm_unavailable__"


def _deterministic_narrative(audience: str, stats: dict) -> str:
    """Guaranteed-grounded fallback, assembled from the stats by string substitution.

    This exists so the failure mode of the grounding check is a plainer report,
    never an ungrounded one. A governance product must not have a code path that
    ships an unverified claim because the model was having a bad day.
    """
    scope = stats.get("scope", "All Apps")
    total = stats.get("total_interactions_evaluated", 0)
    trust = stats.get("avg_trust_score", 100.0)
    flags = stats.get("top_flag_types", "none")
    critical = stats.get("critical_incidents", 0)
    pending = stats.get("pending_human_reviews", 0)
    redacted = stats.get("pii_auto_redacted_count", 0)
    impact = stats.get("total_estimated_business_impact_usd", 0)
    spend = stats.get("total_ai_spend_usd", 0)
    days = stats.get("window_days", 7)

    if audience == "engineer":
        return (
            f"Across {total} evaluated interactions for {scope} over the last {days} days, the average "
            f"TrustScore is {trust}. The most frequent flag types were: {flags}. "
            f"{critical} interaction(s) were classified critical and {pending} are awaiting human review. "
            f"Root-cause attribution is not available at this aggregate level — open the individual traces "
            f"in the Live Feed to see the prompt, response, and per-check evidence behind each flag."
        )
    if audience == "ciso":
        return (
            f"Compliance posture for {scope} over the last {days} days: {total} interactions were evaluated "
            f"with an average TrustScore of {trust}. {redacted} interaction(s) had sensitive data automatically "
            f"redacted before delivery, and {critical} were classified as critical incidents. "
            f"{pending} item(s) are currently held for human review under an SLA timer. "
            f"Estimated business exposure across all flagged interactions is ${impact:,}."
        )
    return (
        f"Our AI systems scored {trust} out of 100 on trust over the last {days} days across {total} "
        f"interactions. Estimated financial exposure from flagged issues is ${impact:,}, and total AI "
        f"spend for the period was ${spend}. {critical} issue(s) were serious enough to be classified "
        f"critical, and {pending} are waiting on a human decision. "
        f"The recommended next step is to clear the pending review queue before the SLA windows expire."
    )


def _call(prompt: str) -> str:
    """Try the judge tier first, then the primary model, then give up.

    Free-tier Gemini quotas are per-model *per day*, not just per minute, so a single
    exhausted model would otherwise drop every narrative onto the deterministic template
    for the rest of the day. Falling back across tiers means the narrator keeps working
    while any model has headroom, and the deterministic template stays as the last resort
    rather than the first thing a quota blip triggers.
    """
    for model in model_chain(get_settings().gemini_judge_model):
        text = generate_text(prompt, model=model, fallback=_UNAVAILABLE)
        text = (text or "").strip()
        if text and text != _UNAVAILABLE:
            return text
    return _UNAVAILABLE


def generate(audience: str, stats: dict) -> dict:
    """Generate a narrative and verify it is grounded in `stats` before returning it.

    Returns {"narrative": str, "grounding": {...}} where grounding.status is one of:
      verified   — the model's first draft passed the check
      corrected  — the first draft was rejected, a regeneration passed
      fallback   — both drafts were rejected; a deterministic narrative was substituted
      unavailable— the upstream LLM could not be reached; deterministic narrative used
    """
    instructions = AUDIENCE_INSTRUCTIONS.get(audience, AUDIENCE_INSTRUCTIONS["ceo"])
    stats_lines = "\n".join(f"- {key}: {value}" for key, value in stats.items())
    # Uses the cheaper/higher-quota judge model tier rather than the primary model: the
    # narrator is internal tooling and shouldn't compete for the same rate limit as the
    # monitored applications' own traffic.
    base_prompt = PROMPT.format(audience=audience, instructions=instructions, stats=stats_lines)

    narrative = _call(base_prompt)
    if narrative == _UNAVAILABLE or not narrative:
        return {
            "narrative": _deterministic_narrative(audience, stats),
            "grounding": {
                "status": "unavailable",
                "passed": True,
                "unsupported_terms": [],
                "attempts": 0,
                "method": "deterministic_template",
            },
        }

    verdict = grounding.check(narrative, stats)
    if verdict["passed"]:
        return {
            "narrative": narrative,
            "grounding": {
                "status": "verified",
                "passed": True,
                "unsupported_terms": [],
                "checked_terms": verdict["checked_terms"],
                "attempts": 1,
                "method": "deterministic_entity_check",
            },
        }

    # One corrective retry, naming the fabrications explicitly.
    retry_prompt = base_prompt + _CORRECTION.format(terms=", ".join(verdict["unsupported_terms"]))
    retry = _call(retry_prompt)
    if retry and retry != _UNAVAILABLE:
        retry_verdict = grounding.check(retry, stats)
        if retry_verdict["passed"]:
            return {
                "narrative": retry,
                "grounding": {
                    "status": "corrected",
                    "passed": True,
                    "unsupported_terms": verdict["unsupported_terms"],
                    "checked_terms": retry_verdict["checked_terms"],
                    "attempts": 2,
                    "method": "deterministic_entity_check",
                },
            }

    return {
        "narrative": _deterministic_narrative(audience, stats),
        "grounding": {
            "status": "fallback",
            "passed": True,
            "unsupported_terms": verdict["unsupported_terms"],
            "attempts": 2,
            "method": "deterministic_template",
        },
    }
