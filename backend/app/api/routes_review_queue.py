import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Escalation, Interaction, utcnow
from app.db.session import get_db
from app.intelligence.escalation import sweep_expired

router = APIRouter(prefix="/api/review-queue")


def _seconds_remaining(escalation: Escalation) -> int | None:
    if escalation.sla_deadline is None:
        return None
    now = utcnow()
    return max(0, int((escalation.sla_deadline - now).total_seconds()))


@router.get("")
def list_queue(status: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    sweep_expired(db)
    query = db.query(Escalation)
    if status:
        query = query.filter(Escalation.status == status)
    else:
        query = query.filter(Escalation.status != "resolved")
    items = query.order_by(Escalation.created_at.desc()).limit(limit).all()

    results = []
    for esc in items:
        interaction = db.get(Interaction, esc.interaction_id)
        results.append(
            {
                "id": esc.id,
                "interaction_id": esc.interaction_id,
                "app_name": interaction.app.name if interaction and interaction.app else None,
                "prompt": interaction.prompt if interaction else None,
                "response": interaction.delivered_response if interaction else None,
                "trust_score": interaction.evaluation.trust_score if interaction and interaction.evaluation else None,
                "flags": interaction.evaluation.flags if interaction and interaction.evaluation else [],
                "decision": esc.decision,
                "status": esc.status,
                "sla_seconds": esc.sla_seconds,
                "seconds_remaining": _seconds_remaining(esc),
                "reviewer_decision": esc.reviewer_decision,
                "created_at": esc.created_at.isoformat(),
            }
        )
    return results


class ReviewDecision(BaseModel):
    action: str  # approve | reject | edit
    note: str | None = None
    edited_response: str | None = None


@router.post("/{escalation_id}/decision")
def decide(escalation_id: int, payload: ReviewDecision, db: Session = Depends(get_db)):
    escalation = db.get(Escalation, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if escalation.status != "pending":
        raise HTTPException(status_code=400, detail=f"Escalation already {escalation.status}")

    escalation.status = {"approve": "approved", "reject": "rejected", "edit": "edited"}.get(payload.action, "approved")
    escalation.reviewer_decision = payload.action
    escalation.reviewer_note = payload.note
    escalation.decided_at = utcnow()
    if payload.action == "edit" and payload.edited_response:
        escalation.edited_response = payload.edited_response
        interaction = db.get(Interaction, escalation.interaction_id)
        if interaction:
            interaction.delivered_response = payload.edited_response

    db.commit()
    return {"ok": True, "status": escalation.status}
