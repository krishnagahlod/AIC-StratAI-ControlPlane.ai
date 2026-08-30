from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_judge_model: str = "gemini-2.5-flash-lite"
    database_url: str = "sqlite:///./controlplane.db"
    # Enables the /api/demo endpoints used to re-arm the Human Review Queue before a
    # recording. Off by default so a deployed instance never exposes them.
    demo_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# $ per 1K tokens, illustrative public pricing tiers used for cost attribution math.
PRICING_TABLE = {
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.5-flash-lite": {"input": 0.00001875, "output": 0.000075},
}
DEFAULT_PRICING = {"input": 0.0005, "output": 0.0015}

# Rule-based (non-LLM) task complexity classifier keyword sets. A simple lexical
# heuristic is deliberately used here instead of an LLM call, since this check
# must stay deterministic and cheap to justify itself as a cost-control signal.
SIMPLE_TASK_KEYWORDS = {
    "hi", "hello", "hey", "thanks", "thank you", "what is your name",
    "what are your hours", "what is the price", "how much does it cost",
    "opening hours", "return policy", "track my order", "reset my password",
}
COMPLEX_TASK_KEYWORDS = {
    "analyze", "compare", "design", "architecture", "strategy", "root cause",
    "reason step by step", "multi-step", "optimize", "diagnose", "synthesize",
    "evaluate the tradeoffs", "write code", "debug",
}
CHEAP_MODEL_TIER = {"gemini-2.5-flash-lite"}
MID_MODEL_TIER = {"gemini-2.5-flash"}
EXPENSIVE_MODEL_TIER = {"gemini-2.5-pro"}

# Illustrative business assumptions used by the Business Impact Scorer. These are
# stated explicitly (per the Round 2 brief's instruction to state assumptions
# clearly) rather than hidden inside formulas.
BUSINESS_ASSUMPTIONS = {
    "avg_order_value_usd": 85.0,
    "customer_lifetime_value_usd": 620.0,
    "churn_probability_per_toxicity_incident": 0.015,
    "gdpr_fine_reference_usd": 20_000_000,
    "gdpr_fine_probability_per_pii_incident": 0.0004,
    "remediation_cost_per_compliance_incident_usd": 1_500.0,
    "reputation_incident_base_cost_usd": 8_000.0,
    "weekly_interactions_per_app": 12_000,
}

# Escalation tiers by TrustScore. SLA is compressed from the architecture doc's
# "5 minutes" to a demo-friendly interval so the auto-default behavior is
# observable live without waiting.
ESCALATION_TIERS = [
    {"min": 90, "max": 100, "decision": "allow_silent"},
    {"min": 70, "max": 89, "decision": "allow_flag_async"},
    {"min": 30, "max": 69, "decision": "escalate_human"},
    {"min": 0, "max": 29, "decision": "auto_block_alert"},
]
ESCALATION_SLA_SECONDS = 120

PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"\b(?:\+?\d{1,2}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b",
}
DATA_LEAKAGE_PATTERNS = {
    "api_key": r"\b(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|AQ\.[A-Za-z0-9_-]{20,})\b",
    "internal_url": r"\bhttps?://(?:jira|confluence|internal|corp)\.[A-Za-z0-9.-]+\S*\b",
}
BLOCKLIST_PATTERNS = [
    r"ignore (all|any|previous|prior) instructions",
    r"disregard (all|any|previous|prior) (instructions|rules)",
    r"reveal (your|the) system prompt",
    r"you are now (in )?(dan|developer) mode",
    r"pretend (you have|to have) no (restrictions|filters)",
]
TOXICITY_QUICK_PATTERNS = [
    r"\bkill yourself\b",
    r"\b(you|they|he|she) (are|is) (stupid|worthless|subhuman)\b",
]
