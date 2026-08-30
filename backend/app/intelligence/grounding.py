"""Deterministic grounding check for LLM-generated narratives.

ControlPlane.ai's whole thesis is that LLM output should not be trusted on
presentation alone. The Executive Narrator is itself an LLM feature, so it gets
held to the same standard as the applications we monitor: every entity it names
must be traceable to the data it was given.

This check is deliberately *deterministic* rather than a second LLM-as-judge call:
a grounding guarantee that itself depends on a probabilistic model is not a
guarantee. It is also free, instant, and auditable — a reviewer can read this
module and know exactly what was enforced.

Detection strategy: the failure mode we observed (and are defending against) is
the model inventing plausible-sounding *system nouns* — `CustomerSupportAgent`,
a `UserAuth` microservice — that appear nowhere in the aggregate stats. So we
extract the token classes those fabrications land in and require each one to be
reconstructible from the allowed vocabulary.
"""

from __future__ import annotations

import re

# Ordinary domain language the narrator is entitled to use without it appearing
# verbatim in the stats. These are concepts, standards, and metric names — not
# claims about the customer's systems, which is what we actually guard.
DOMAIN_VOCAB: set[str] = {
    # product / platform
    "controlplane", "controlplane.ai", "trustscore", "trust", "score", "scores",
    "control", "plane", "data", "intelligence", "layer", "platform", "dashboard",
    "executive", "narrator", "business", "impact", "policy", "playground",
    # evaluation dimensions & metrics
    "performance", "cost", "responsibility", "faithfulness", "coherence",
    "completeness", "confidence", "calibration", "precision", "recall",
    "latency", "throughput", "budget", "spend", "tokens", "token",
    # risk / flag vocabulary
    "hallucination", "hallucinations", "pii", "leak", "leakage", "bias",
    "toxicity", "safety", "violation", "violations", "jailbreak", "prompt",
    "injection", "redaction", "redacted", "auto", "blocked", "escalation",
    "escalated", "incident", "incidents", "critical", "risk", "flag", "flags",
    "mismatch", "redundant", "hedging", "drift", "guardrail", "guardrails",
    # regulatory / compliance
    "gdpr", "eu", "ai", "act", "hipaa", "ccpa", "soc", "iso", "nist",
    "regulatory", "compliance", "audit", "auditor", "regulator",
    # technical generics
    "llm", "llms", "rag", "retrieval", "augmented", "generation", "model",
    "models", "api", "sla", "slas", "pipeline", "proxy", "judge", "rule",
    "deterministic", "async", "sync", "review", "reviewer", "queue", "human",
    # roles
    "ciso", "ceo", "cto", "engineer", "engineering", "officer", "team",
    # connectors, so a multi-word name is never rejected on its glue words
    "and", "or", "of", "the", "for", "with", "in", "on", "to", "a", "an",
}

# Nouns that signal the model is naming a *system* rather than a concept. A
# capitalised phrase containing one of these is exactly the shape of the
# fabrications we caught, so those phrases get checked even in plain prose.
_SYSTEM_NOUNS = {
    "service", "services", "microservice", "microservices", "agent", "agents",
    "pipeline", "module", "cluster", "endpoint", "database", "bot", "tool",
    "copilot", "system", "systems", "app", "application", "server", "gateway",
}

_BACKTICKED = re.compile(r"`([^`]+)`")
_PASCAL_CASE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
_SNAKE_CASE = re.compile(r"\b[a-z0-9]+(?:_[a-z0-9]+)+\b")
# Capitalised words joined only by spaces/hyphens — never across a connector like
# "and", which would glue two legitimate names into one phantom entity.
_CAP_PHRASE = re.compile(r"\b[A-Z][a-z0-9]+(?:[ -][A-Z][a-z0-9]+){0,4}\b")
_WORD_SPLIT = re.compile(r"[^a-z0-9.]+")


def _words(term: str) -> list[str]:
    """Normalise a term into comparable lowercase words.

    Handles the three shapes an identifier arrives in: PascalCase is split on
    case boundaries, snake_case and kebab-case on their separators, and plain
    phrases on whitespace.
    """
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", term)
    return [w for w in _WORD_SPLIT.split(spaced.lower()) if w]


def build_allowed_vocab(stats: dict) -> set[str]:
    """Every word the narrator may use to name something in the customer's world."""
    allowed = set(DOMAIN_VOCAB)
    for value in stats.values():
        for word in _words(str(value)):
            allowed.add(word)
    return allowed


def _is_supported(term: str, allowed: set[str]) -> bool:
    words = _words(term)
    if not words:
        return True
    # Pure numbers/units are handled by the prompt's numeric guardrail, not here.
    if all(w.replace(".", "").isdigit() for w in words):
        return True
    return all(w in allowed for w in words)


def _sentence_initial_words(text: str) -> set[str]:
    """Words that are only capitalised because they start a sentence.

    Without this, "Overall trust improved." would look like a proper noun.
    """
    return {m.group(1) for m in re.finditer(r"(?:^|[.!?]\s+)([A-Z][a-z0-9]+)", text)}


def check(narrative: str, stats: dict) -> dict:
    """Return a grounding verdict for one generated narrative.

    {"passed": bool, "unsupported_terms": [...], "checked_terms": int}
    """
    allowed = build_allowed_vocab(stats)
    sentence_starts = _sentence_initial_words(narrative)
    candidates: list[str] = []

    candidates.extend(_BACKTICKED.findall(narrative))
    candidates.extend(_PASCAL_CASE.findall(narrative))
    candidates.extend(_SNAKE_CASE.findall(narrative))

    # Capitalised prose phrases only matter when they name a system — a plain
    # capitalised phrase is usually a heading-style noun, not a fabricated
    # service, and flagging those would cost us good narratives for nothing.
    for phrase in _CAP_PHRASE.findall(narrative):
        phrase = phrase.strip()
        if phrase in sentence_starts and " " not in phrase:
            continue
        if any(w in _SYSTEM_NOUNS for w in _words(phrase)):
            candidates.append(phrase)

    unsupported: list[str] = []
    seen: set[str] = set()
    for term in candidates:
        key = term.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        if not _is_supported(term, allowed):
            unsupported.append(term.strip())

    return {
        "passed": not unsupported,
        "unsupported_terms": unsupported,
        "checked_terms": len(seen),
    }
