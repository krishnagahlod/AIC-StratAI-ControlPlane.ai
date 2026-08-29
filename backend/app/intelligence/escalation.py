import datetime

from app.config import ESCALATION_SLA_SECONDS, ESCALATION_TIERS
from app.db.models import Escalation, utcnow

CRITICAL_SLA_SECONDS = 30
_PII_ONLY_TYPES = {"pii_leak", "data_leakage", "budget_near_limit"}


_TIERS_BY_MIN_DESC = sorted(ESCALATION_TIERS, key=lambda t: t["min"], reverse=True)


def _tier_for_score(trust_score: float) -> str:
    for tier in _TIERS_BY_MIN_DESC:
        if trust_score >= tier["min"]:
            return tier["decision"]
    return _TIERS_BY_MIN_DESC[-1]["decision"]


def decide(trust_score: float, flags: list[dict]) -> dict:
    tier = _tier_for_score(trust_score)
    non_pii_types = {f["type"] for f in flags} - _PII_ONLY_TYPES
    has_critical_safety = any(f["type"] == "safety_violation" and f["severity"] == "critical" for f in flags)
    override_applied = None

    if has_critical_safety:
        tier = "auto_block_alert"
        override_applied = "critical_safety_violation_forced_block"
    elif tier in ("escalate_human", "auto_block_alert") and not non_pii_types:
        tier = "allow_flag_async"
        override_applied = "pii_already_auto_redacted_no_other_issue"

    return {"decision": tier, "override_applied": override_applied}


def build_escalation(interaction_id: int, decision: str) -> Escalation:
    now = utcnow()
    if decision == "escalate_human":
        return Escalation(
            interaction_id=interaction_id,
            decision=decision,
            status="pending",
            sla_seconds=ESCALATION_SLA_SECONDS,
            sla_deadline=now + datetime.timedelta(seconds=ESCALATION_SLA_SECONDS),
        )
    if decision == "auto_block_alert":
        return Escalation(
            interaction_id=interaction_id,
            decision=decision,
            status="pending",
            sla_seconds=CRITICAL_SLA_SECONDS,
            sla_deadline=now + datetime.timedelta(seconds=CRITICAL_SLA_SECONDS),
        )
    return Escalation(interaction_id=interaction_id, decision=decision, status="resolved")


def sweep_expired(db) -> int:
    now = utcnow()
    expired = (
        db.query(Escalation)
        .filter(Escalation.status == "pending", Escalation.sla_deadline.isnot(None), Escalation.sla_deadline < now)
        .all()
    )
    for escalation in expired:
        escalation.status = "auto_defaulted"
        escalation.reviewer_decision = "safe_default_applied"
        escalation.decided_at = now
    if expired:
        db.commit()
    return len(expired)
