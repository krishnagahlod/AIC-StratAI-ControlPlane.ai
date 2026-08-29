from app.config import get_settings
from app.proxy.llm_client import generate_text

AUDIENCE_INSTRUCTIONS = {
    "engineer": (
        "Write for an ML engineer. Be technical and specific: name flag types, affected apps, "
        "faithfulness/coherence issues, and concrete pipeline fixes. 3-5 sentences."
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

Write the report now as plain prose (no markdown headers, no bullet lists), in the voice of a
confident but honest internal report. Do not invent numbers beyond what's given.
"""


def generate(audience: str, stats: dict) -> str:
    instructions = AUDIENCE_INSTRUCTIONS.get(audience, AUDIENCE_INSTRUCTIONS["ceo"])
    stats_lines = "\n".join(f"- {key}: {value}" for key, value in stats.items())
    prompt = PROMPT.format(audience=audience, instructions=instructions, stats=stats_lines)
    # Uses the cheaper/higher-quota judge model tier rather than the primary model: the
    # narrator is internal tooling and shouldn't compete for the same rate limit as the
    # monitored applications' own traffic.
    return generate_text(prompt, model=get_settings().gemini_judge_model).strip()
