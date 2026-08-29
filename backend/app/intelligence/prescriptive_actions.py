from app.proxy.llm_client import generate_judge_json

PATTERN_TABLE = {
    "hallucination_numeric_mismatch": {
        "root_cause": "The response introduced a numeric claim absent from the retrieved source context — likely a context window/chunking gap in the RAG pipeline.",
        "action": "Enable document chunking with ~200-token overlap and re-rank retrieved chunks by relevance before generation.",
        "expected_impact": "~12% reduction in numeric hallucinations on long-document queries.",
        "estimated_value_usd": 34000,
        "confidence": 0.78,
    },
    "hallucination_llm_judge": {
        "root_cause": "The model fabricated a claim not grounded in the provided context or is answering outside its verified knowledge.",
        "action": "Add a mandatory retrieval-grounding step before generation and instruct the model to explicitly abstain when no source supports a claim.",
        "expected_impact": "Meaningful reduction in ungrounded claims delivered to end users.",
        "estimated_value_usd": 22000,
        "confidence": 0.7,
    },
    "model_overuse": {
        "root_cause": "A high-cost model tier is being used for simple/FAQ-style tasks that a cheaper tier could handle.",
        "action": "Add a lightweight pre-routing classifier that sends simple/FAQ tasks to a cheaper model tier.",
        "expected_impact": "Meaningful reduction in per-response cost for this task category with minimal quality loss.",
        "estimated_value_usd": 2100,
        "confidence": 0.82,
    },
    "agent_loop_suspected": {
        "root_cause": "An agent/chain is repeating similar calls without converging — likely missing a termination condition.",
        "action": "Add a hard max_iterations limit (e.g. 5) and a similarity-based early-stop check between successive agent steps.",
        "expected_impact": "~$2,100/month savings and elimination of runaway-loop incidents.",
        "estimated_value_usd": 2100,
        "confidence": 0.85,
    },
    "redundant_call": {
        "root_cause": "Near-identical prompts are being re-sent within a short window instead of being served from cache.",
        "action": "Introduce a short-TTL semantic cache keyed on normalized prompt + app for repeat queries.",
        "expected_impact": "Removes duplicate LLM spend for repeat questions.",
        "estimated_value_usd": 400,
        "confidence": 0.8,
    },
    "pii_leak": {
        "root_cause": "The model is exposing personal data present in its context/training or retrieved documents.",
        "action": "Add a mandatory output PII filter ahead of delivery and audit the underlying knowledge base/training data for unredacted PII.",
        "expected_impact": "Eliminates PII leakage to end users, reducing regulatory exposure.",
        "estimated_value_usd": 50000,
        "confidence": 0.75,
    },
    "bias": {
        "root_cause": "The prompt template or underlying content uses non-neutral, demographically-coded language.",
        "action": "Update the prompt template to gender-/demographic-neutral framing and add a bias regression test to CI.",
        "expected_impact": "~60% reduction in bias flags for this app.",
        "estimated_value_usd": 8000,
        "confidence": 0.68,
    },
    "safety_violation": {
        "root_cause": "The assistant is giving definitive advice in a regulated domain (medical/legal/financial) it isn't authorized to give.",
        "action": "Add an explicit policy guardrail that redirects regulated-domain questions to a disclaimer + human/licensed-professional referral.",
        "expected_impact": "Removes a major compliance liability class entirely.",
        "estimated_value_usd": 75000,
        "confidence": 0.8,
    },
    "prompt_injection": {
        "root_cause": "Users are attempting to override system instructions via crafted prompts.",
        "action": "Harden the system prompt, add an input-classification guardrail ahead of the model, and log/alert on injection attempts.",
        "expected_impact": "Reduces successful jailbreak rate and associated downstream risk.",
        "estimated_value_usd": 15000,
        "confidence": 0.72,
    },
}

LLM_FALLBACK_PROMPT = """Given these AI governance flags for an enterprise application named "{app_name}":
{flags}

Propose one prescriptive fix. Return strict JSON:
{{
  "root_cause": "one sentence",
  "action": "one concrete, specific action",
  "expected_impact": "one sentence with a rough magnitude",
  "estimated_value_usd": number,
  "confidence": 0.0-1.0
}}"""


def _rank(flags: list[dict]) -> list[dict]:
    severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    return sorted(flags, key=lambda f: severity_rank.get(f["severity"], 0), reverse=True)


def generate_rule_based(app, flags: list[dict]) -> dict | None:
    if not flags:
        return None
    lead = _rank(flags)[0]
    template = PATTERN_TABLE.get(lead["type"])
    if not template:
        return None
    return {
        "issue": f"{lead['type'].replace('_', ' ').title()} detected in {app.name}",
        "root_cause": template["root_cause"],
        "action": template["action"],
        "expected_impact": template["expected_impact"],
        "estimated_value_usd": template["estimated_value_usd"],
        "confidence": template["confidence"],
        "method": "rule_based",
    }


def generate_for_interaction(app, flags: list[dict]) -> dict | None:
    if not flags:
        return None

    rule_based = generate_rule_based(app, flags)
    if rule_based:
        return rule_based

    ranked = _rank(flags)
    lead = ranked[0]
    if lead["severity"] not in ("high", "critical"):
        return None

    flags_desc = "\n".join(f"- {f['type']} ({f['severity']}): {f['detail']}" for f in ranked)
    result = generate_judge_json(LLM_FALLBACK_PROMPT.format(app_name=app.name, flags=flags_desc))
    if not result:
        return None

    return {
        "issue": f"{lead['type'].replace('_', ' ').title()} detected in {app.name}",
        "root_cause": result.get("root_cause", "Not determined"),
        "action": result.get("action", "Manual investigation recommended"),
        "expected_impact": result.get("expected_impact", "Unquantified"),
        "estimated_value_usd": float(result.get("estimated_value_usd", 0) or 0),
        "confidence": float(result.get("confidence", 0.5) or 0.5),
        "method": "llm_generated",
    }
