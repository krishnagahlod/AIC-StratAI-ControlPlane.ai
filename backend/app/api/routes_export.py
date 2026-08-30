"""Compliance evidence export.

A CISO's actual deliverable is not a dashboard — it is an artifact they can hand to an
auditor or regulator showing what the AI did, what the platform checked, how each finding
was detected, who decided what, and when. Our market research found this workflow is
underserved by evaluation-focused competitors.

The export deliberately carries the **detection method** for every flag (deterministic
rule vs. LLM-as-judge). That distinction is the Round 2 brief's explicit ask, and it is
exactly what an auditor needs in order to weigh the finding: a regex match is
reproducible evidence, a model judgement is not.

No PDF dependency: the evidence pack is served as JSON and CSV, and the frontend renders
a print-optimised page the browser turns into a PDF.
"""

import csv
import datetime
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.models import App, BusinessImpact, Escalation, Evaluation, Interaction, utcnow
from app.db.session import get_db

router = APIRouter(prefix="/api")


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.isoformat() + ("Z" if value.tzinfo is None else "")
    return str(value)


def _evidence_for(db: Session, interaction: Interaction) -> dict:
    app = db.get(App, interaction.app_id)
    evaluation = db.query(Evaluation).filter(Evaluation.interaction_id == interaction.id).first()
    impact = db.query(BusinessImpact).filter(BusinessImpact.interaction_id == interaction.id).first()
    esc = db.query(Escalation).filter(Escalation.interaction_id == interaction.id).first()

    flags = evaluation.flags if evaluation else []
    return {
        "evidence_pack_version": "1.0",
        "generated_at": _iso(utcnow()),
        "interaction": {
            "id": interaction.id,
            "timestamp": _iso(interaction.created_at),
            "application": app.name if app else None,
            "application_type": app.app_type if app else None,
            "task_type": interaction.task_type,
            "model": interaction.model,
            "latency_ms": round(interaction.latency_ms or 0, 1),
            "input_tokens": interaction.input_tokens,
            "output_tokens": interaction.output_tokens,
            "source": interaction.source,
        },
        "content": {
            "prompt": interaction.prompt,
            "source_context": interaction.rag_context,
            # Both versions are retained: an auditor needs to see what the model produced
            # as well as what the end user actually received.
            "raw_model_output": interaction.raw_response,
            "delivered_to_user": interaction.delivered_response,
            "was_modified_before_delivery": interaction.raw_response != interaction.delivered_response,
        },
        "controls_applied": {
            "sync_action": interaction.sync_action,
            "sync_flags": interaction.sync_flags,
        },
        "evaluation": None
        if evaluation is None
        else {
            "trust_score": evaluation.trust_score,
            "risk_level": evaluation.risk_level,
            "performance_score": evaluation.performance_score,
            "cost_score": evaluation.cost_score,
            "responsibility_score": evaluation.responsibility_score,
            "policy_weights": {
                "performance": app.weight_performance if app else None,
                "cost": app.weight_cost if app else None,
                "responsibility": app.weight_responsibility if app else None,
            },
            "estimated_cost_usd": evaluation.response_cost_usd,
            "findings": [
                {
                    "type": f.get("type"),
                    "dimension": f.get("dimension"),
                    "severity": f.get("severity"),
                    # The distinction an auditor needs: reproducible rule vs. model judgement.
                    "detection_method": "LLM-as-judge" if f.get("method") == "llm_judge" else "Deterministic rule",
                    "finding": f.get("detail"),
                    "evidence": f.get("evidence"),
                    "action_taken": f.get("action_taken"),
                }
                for f in flags
            ],
        },
        "business_impact": None
        if impact is None
        else {
            "risk_category": impact.risk_category,
            "estimated_impact_usd": impact.estimated_impact_usd,
            "affected_users": impact.affected_users,
            "confidence": impact.confidence,
            "basis": impact.narrative,
            "note": "Estimated from documented assumptions in backend/app/config.py (BUSINESS_ASSUMPTIONS), not measured loss.",
        },
        "governance_decision": None
        if esc is None
        else {
            "decision": esc.decision,
            "status": esc.status,
            "sla_seconds": esc.sla_seconds,
            "sla_deadline": _iso(esc.sla_deadline),
            "reviewer_decision": esc.reviewer_decision,
            "reviewer_note": esc.reviewer_note,
            "decided_at": _iso(esc.decided_at),
        },
    }


@router.get("/interactions/{interaction_id}/evidence")
def interaction_evidence(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.get(Interaction, interaction_id)
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _evidence_for(db, interaction)


@router.get("/export/flagged.csv")
def export_flagged_csv(app_id: int | None = None, days: int = 14, db: Session = Depends(get_db)):
    """One row per finding across the period — the aggregate an auditor samples from."""
    since = utcnow() - datetime.timedelta(days=days)
    query = (
        db.query(Interaction, Evaluation, App)
        .join(Evaluation, Evaluation.interaction_id == Interaction.id)
        .join(App, App.id == Interaction.app_id)
        .filter(Interaction.created_at >= since)
    )
    if app_id is not None:
        query = query.filter(Interaction.app_id == app_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "interaction_id", "timestamp_utc", "application", "task_type", "model",
        "trust_score", "risk_level", "sync_action",
        "finding_type", "dimension", "severity", "detection_method", "finding_detail",
        "action_taken", "estimated_impact_usd", "governance_decision", "review_status",
    ])

    rows_written = 0
    for interaction, evaluation, app in query.order_by(Interaction.created_at.desc()).all():
        if not evaluation.flags:
            continue
        impact = db.query(BusinessImpact).filter(BusinessImpact.interaction_id == interaction.id).first()
        esc = db.query(Escalation).filter(Escalation.interaction_id == interaction.id).first()
        for f in evaluation.flags:
            writer.writerow([
                interaction.id,
                _iso(interaction.created_at),
                app.name,
                interaction.task_type,
                interaction.model,
                evaluation.trust_score,
                evaluation.risk_level,
                interaction.sync_action,
                f.get("type"),
                f.get("dimension"),
                f.get("severity"),
                "LLM-as-judge" if f.get("method") == "llm_judge" else "Deterministic rule",
                f.get("detail"),
                f.get("action_taken") or "",
                impact.estimated_impact_usd if impact else "",
                esc.decision if esc else "",
                esc.status if esc else "",
            ])
            rows_written += 1

    filename = f"controlplane-findings-{utcnow().date().isoformat()}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Row-Count": str(rows_written),
        },
    )
