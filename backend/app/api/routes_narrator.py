import datetime
import time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import App, BusinessImpact, Escalation, Evaluation, Interaction, utcnow
from app.db.session import get_db
from app.intelligence import executive_narrator

router = APIRouter(prefix="/api/narrator")

# An executive health report does not need regenerating every 90 seconds, and a short
# TTL means repeated tab-switching burns the free-tier rate limit and drops the page
# onto the deterministic fallback. Ten minutes matches how the artifact is actually read.
_CACHE_TTL_SECONDS = 600
_cache: dict[tuple, tuple[float, dict]] = {}


def _collect_stats(db: Session, app_id: int | None, days: int) -> dict:
    since = utcnow() - datetime.timedelta(days=days)
    base = db.query(Evaluation).join(Interaction).filter(Interaction.created_at >= since)
    if app_id is not None:
        base = base.filter(Interaction.app_id == app_id)
    evaluations = base.all()

    total = len(evaluations)
    avg_trust = round(sum(e.trust_score for e in evaluations) / total, 1) if total else 100.0

    flag_counts: dict[str, int] = {}
    for e in evaluations:
        for f in e.flags:
            flag_counts[f["type"]] = flag_counts.get(f["type"], 0) + 1
    top_flags = sorted(flag_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]

    impact_query = db.query(func.sum(BusinessImpact.estimated_impact_usd)).join(
        Interaction, Interaction.id == BusinessImpact.interaction_id
    ).filter(Interaction.created_at >= since)
    if app_id is not None:
        impact_query = impact_query.filter(Interaction.app_id == app_id)
    total_impact = impact_query.scalar() or 0

    total_cost = sum(e.response_cost_usd for e in evaluations)
    pii_auto_redacted = sum(1 for e in evaluations for f in e.flags if f["type"] in ("pii_leak", "data_leakage") and f.get("action_taken") == "auto_redacted")
    critical_count = sum(1 for e in evaluations if e.risk_level == "critical")
    pending_reviews = db.query(func.count(Escalation.id)).filter(Escalation.status == "pending").scalar() or 0

    app_name = "All Apps"
    if app_id is not None:
        app = db.get(App, app_id)
        app_name = app.name if app else app_name

    # The narrator is told to name applications, so it needs the real names. Without
    # them it has no true nouns to reference and invents plausible ones instead —
    # this list is queried live so it can never drift from what's actually monitored.
    if app_id is not None:
        monitored = [app_name]
    else:
        monitored = [name for (name,) in db.query(App.name).order_by(App.id).all()]

    return {
        "scope": app_name,
        "window_days": days,
        "monitored_applications": ", ".join(monitored) or "none",
        "total_interactions_evaluated": total,
        "avg_trust_score": avg_trust,
        "top_flag_types": ", ".join(f"{t} x{c}" for t, c in top_flags) or "none",
        "critical_incidents": critical_count,
        "pending_human_reviews": pending_reviews,
        "pii_auto_redacted_count": pii_auto_redacted,
        # Whole dollars: no executive report shows cents on a six-figure estimate,
        # and the underlying figure is an estimate from stated assumptions anyway.
        "total_estimated_business_impact_usd": round(total_impact),
        "total_ai_spend_usd": round(total_cost, 4),
    }


@router.get("")
def get_narrative(audience: str = "ceo", app_id: int | None = None, days: int = 7, db: Session = Depends(get_db)):
    cache_key = (audience, app_id, days)
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return {**cached[1], "cached": True}

    stats = _collect_stats(db, app_id, days)
    result = executive_narrator.generate(audience, stats)
    payload = {"narrative": result["narrative"], "grounding": result["grounding"], "stats": stats}
    _cache[cache_key] = (now, payload)
    return {**payload, "cached": False}
