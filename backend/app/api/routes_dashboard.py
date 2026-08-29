import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import BUSINESS_ASSUMPTIONS
from app.db.models import Alert, App, BusinessImpact, Escalation, Evaluation, Interaction, Recommendation, utcnow
from app.db.session import get_db

router = APIRouter(prefix="/api")


def _today_spend_by_app(db: Session) -> dict[int, float]:
    start_of_day = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(Interaction.app_id, func.sum(Evaluation.response_cost_usd))
        .join(Evaluation, Evaluation.interaction_id == Interaction.id)
        .filter(Interaction.created_at >= start_of_day)
        .group_by(Interaction.app_id)
        .all()
    )
    return {app_id: total or 0.0 for app_id, total in rows}


@router.get("/apps")
def list_apps(db: Session = Depends(get_db)):
    apps = db.query(App).all()
    spend_by_app = _today_spend_by_app(db)
    return [
        {
            "id": a.id,
            "key": a.key,
            "name": a.name,
            "app_type": a.app_type,
            "risk_tolerance": a.risk_tolerance,
            "latency_budget_ms": a.latency_budget_ms,
            "weights": {"performance": a.weight_performance, "cost": a.weight_cost, "responsibility": a.weight_responsibility},
            "daily_budget_usd": a.daily_budget_usd,
            "daily_spend_usd": round(spend_by_app.get(a.id, 0.0), 4),
            "budget_remaining_pct": round(max(a.daily_budget_usd - spend_by_app.get(a.id, 0.0), 0) / a.daily_budget_usd * 100, 1)
            if a.daily_budget_usd
            else 0.0,
        }
        for a in apps
    ]


def _interaction_summary(interaction: Interaction) -> dict:
    ev = interaction.evaluation
    bi = interaction.business_impact
    esc = interaction.escalation
    return {
        "id": interaction.id,
        "app_id": interaction.app_id,
        "app_name": interaction.app.name if interaction.app else None,
        "created_at": interaction.created_at.isoformat(),
        "task_type": interaction.task_type,
        "prompt": interaction.prompt,
        "response": interaction.delivered_response,
        "model": interaction.model,
        "latency_ms": interaction.latency_ms,
        "sync_action": interaction.sync_action,
        "sync_flags": interaction.sync_flags,
        "source": interaction.source,
        "evaluation": None
        if ev is None
        else {
            "performance_score": ev.performance_score,
            "cost_score": ev.cost_score,
            "responsibility_score": ev.responsibility_score,
            "trust_score": ev.trust_score,
            "risk_level": ev.risk_level,
            "response_cost_usd": ev.response_cost_usd,
            "flags": ev.flags,
        },
        "business_impact": None
        if bi is None
        else {
            "risk_category": bi.risk_category,
            "estimated_impact_usd": bi.estimated_impact_usd,
            "affected_users": bi.affected_users,
            "confidence": bi.confidence,
            "narrative": bi.narrative,
        },
        "escalation": None
        if esc is None
        else {
            "decision": esc.decision,
            "status": esc.status,
            "sla_seconds": esc.sla_seconds,
            "sla_deadline": esc.sla_deadline.isoformat() if esc.sla_deadline else None,
        },
    }


@router.get("/interactions")
def list_interactions(
    app_id: int | None = None,
    since_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Interaction)
    if app_id is not None:
        query = query.filter(Interaction.app_id == app_id)
    if since_id is not None:
        query = query.filter(Interaction.id > since_id)
    interactions = query.order_by(Interaction.created_at.desc(), Interaction.id.desc()).limit(limit).all()
    return [_interaction_summary(i) for i in reversed(interactions)]


@router.get("/interactions/{interaction_id}")
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.get(Interaction, interaction_id)
    if interaction is None:
        return {"error": "not found"}
    summary = _interaction_summary(interaction)
    summary["raw_response"] = interaction.raw_response
    summary["rag_context"] = interaction.rag_context
    return summary


@router.get("/trends")
def get_trends(app_id: int | None = None, days: int = 14, db: Session = Depends(get_db)):
    since = utcnow() - datetime.timedelta(days=days)
    query = (
        db.query(
            func.date(Interaction.created_at).label("day"),
            func.avg(Evaluation.trust_score).label("avg_trust_score"),
            func.avg(Evaluation.performance_score).label("avg_performance"),
            func.avg(Evaluation.cost_score).label("avg_cost"),
            func.avg(Evaluation.responsibility_score).label("avg_responsibility"),
            func.sum(Evaluation.response_cost_usd).label("total_cost_usd"),
            func.count(Evaluation.id).label("count"),
        )
        .join(Interaction, Interaction.id == Evaluation.interaction_id)
        .filter(Interaction.created_at >= since)
    )
    if app_id is not None:
        query = query.filter(Interaction.app_id == app_id)
    rows = query.group_by(func.date(Interaction.created_at)).order_by(func.date(Interaction.created_at)).all()

    return [
        {
            "day": str(row.day),
            "avg_trust_score": round(row.avg_trust_score or 0, 1),
            "avg_performance": round(row.avg_performance or 0, 1),
            "avg_cost": round(row.avg_cost or 0, 1),
            "avg_responsibility": round(row.avg_responsibility or 0, 1),
            "total_cost_usd": round(row.total_cost_usd or 0, 4),
            "count": row.count,
        }
        for row in rows
    ]


@router.get("/alerts")
def list_alerts(limit: int = 20, db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.updated_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "severity": a.severity,
            "message": a.message,
            "count": a.count,
            "app_id": a.app_id,
            "interaction_id": a.interaction_id,
            "updated_at": a.updated_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/recommendations")
def list_recommendations(app_id: int | None = None, limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(Recommendation)
    if app_id is not None:
        query = query.filter(Recommendation.app_id == app_id)
    recs = query.order_by(Recommendation.priority.asc(), Recommendation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "app_id": r.app_id,
            "priority": r.priority,
            "issue": r.issue,
            "root_cause": r.root_cause,
            "action": r.action,
            "expected_impact": r.expected_impact,
            "estimated_value_usd": r.estimated_value_usd,
            "confidence": r.confidence,
            "method": r.method,
            "created_at": r.created_at.isoformat(),
        }
        for r in recs
    ]


@router.get("/impact-breakdown")
def impact_breakdown(app_id: int | None = None, days: int = 14, db: Session = Depends(get_db)):
    since = utcnow() - datetime.timedelta(days=days)
    query = (
        db.query(
            BusinessImpact.risk_category,
            func.sum(BusinessImpact.estimated_impact_usd).label("total_usd"),
            func.count(BusinessImpact.id).label("count"),
        )
        .join(Interaction, Interaction.id == BusinessImpact.interaction_id)
        .filter(Interaction.created_at >= since, BusinessImpact.risk_category != "none")
    )
    if app_id is not None:
        query = query.filter(Interaction.app_id == app_id)
    rows = query.group_by(BusinessImpact.risk_category).order_by(func.sum(BusinessImpact.estimated_impact_usd).desc()).all()
    return [{"risk_category": r.risk_category, "total_usd": round(r.total_usd or 0, 2), "count": r.count} for r in rows]


@router.get("/summary")
def get_summary(days: int = 7, db: Session = Depends(get_db)):
    since = utcnow() - datetime.timedelta(days=days)
    total = db.query(func.count(Evaluation.id)).join(Interaction).filter(Interaction.created_at >= since).scalar() or 0
    avg_trust = (
        db.query(func.avg(Evaluation.trust_score)).join(Interaction).filter(Interaction.created_at >= since).scalar() or 0
    )
    total_impact = (
        db.query(func.sum(BusinessImpact.estimated_impact_usd))
        .join(Interaction, Interaction.id == BusinessImpact.interaction_id)
        .filter(Interaction.created_at >= since)
        .scalar()
        or 0
    )
    total_cost = (
        db.query(func.sum(Evaluation.response_cost_usd)).join(Interaction).filter(Interaction.created_at >= since).scalar() or 0
    )
    pending_review = db.query(func.count(Escalation.id)).filter(Escalation.status == "pending").scalar() or 0
    critical_count = (
        db.query(func.count(Evaluation.id))
        .join(Interaction)
        .filter(Interaction.created_at >= since, Evaluation.risk_level == "critical")
        .scalar()
        or 0
    )

    return {
        "window_days": days,
        "total_interactions": total,
        "avg_trust_score": round(avg_trust, 1),
        "total_business_impact_usd": round(total_impact, 2),
        "total_ai_spend_usd": round(total_cost, 4),
        "pending_human_reviews": pending_review,
        "critical_incidents": critical_count,
        "assumptions": BUSINESS_ASSUMPTIONS,
    }
