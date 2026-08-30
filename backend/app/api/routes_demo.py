"""Demo-support endpoints.

The Human Review Queue's SLA windows are 30-120 seconds. That is the intended
product behaviour — safe defaults apply fast — but it makes the queue impossible
to film reliably: a pending item can expire between takes.

This router lets an operator re-arm the demo without re-running the seed script
from a terminal, and give the pending items a window long enough to survive a
retake. It is gated behind an explicit setting and documented in the README
rather than hidden, because a governance product should not ship an undisclosed
way to manufacture its own state.
"""

import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Escalation, Interaction, utcnow
from app.db.session import get_db

router = APIRouter(prefix="/api/demo")

# Long enough that a scene can be shot, reviewed, and re-shot without the queue
# emptying itself mid-take.
DEMO_SLA_SECONDS = 600


def _require_demo_mode() -> None:
    if not get_settings().demo_mode:
        raise HTTPException(
            status_code=404,
            detail="Demo endpoints are disabled. Set DEMO_MODE=1 in the backend .env to enable them.",
        )


@router.get("/status")
def demo_status(db: Session = Depends(get_db)):
    pending = db.query(Escalation).filter(Escalation.status == "pending").count()
    return {"demo_mode": get_settings().demo_mode, "pending_reviews": pending}


@router.post("/arm-review-queue")
def arm_review_queue(db: Session = Depends(get_db)):
    """Re-open the most recent human-review escalations with a long SLA window.

    Deliberately reuses escalations that genuinely reached a human-review decision
    rather than fabricating new ones — the queue still shows real evaluated
    interactions, only their timers are extended.
    """
    _require_demo_mode()

    rows = (
        db.query(Escalation, Interaction)
        .join(Interaction, Interaction.id == Escalation.interaction_id)
        .filter(Escalation.decision.in_(["escalate_human", "auto_block_alert"]))
        .order_by(Interaction.created_at.desc())
        .limit(60)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=409, detail="No human-review escalations exist. Run the seed script first.")

    # Pick a *varied* set. Taking the three most recent tends to return the same app
    # and even the same prompt twice, which reads as a rendering bug on screen rather
    # than a queue. Prefer distinct prompts, then spread across apps and decision types.
    selected: list[Escalation] = []
    seen_prompts: set[str] = set()
    seen_apps: set[int] = set()
    seen_decisions: set[str] = set()

    for pass_no in (1, 2):
        for esc, interaction in rows:
            if len(selected) >= 3:
                break
            if interaction.prompt in seen_prompts:
                continue
            # First pass insists on a new app and a new decision type; the second pass
            # relaxes that so we still fill the queue on narrower datasets.
            if pass_no == 1 and (interaction.app_id in seen_apps and esc.decision in seen_decisions):
                continue
            selected.append(esc)
            seen_prompts.add(interaction.prompt)
            seen_apps.add(interaction.app_id)
            seen_decisions.add(esc.decision)

    candidates = selected

    # Resolve whatever is already pending so the queue ends up as exactly the set we
    # armed. Otherwise repeated arming accumulates leftovers and the shot is different
    # every take.
    for stale in db.query(Escalation).filter(Escalation.status == "pending").all():
        if stale not in candidates:
            stale.status = "auto_defaulted"
            stale.decided_at = utcnow()

    now = utcnow()
    for esc in candidates:
        esc.status = "pending"
        esc.sla_seconds = DEMO_SLA_SECONDS
        esc.sla_deadline = now + datetime.timedelta(seconds=DEMO_SLA_SECONDS)
        esc.decided_at = None
        esc.reviewer_decision = None
        esc.reviewer_note = None
    db.commit()

    return {
        "ok": True,
        "armed": len(candidates),
        "sla_seconds": DEMO_SLA_SECONDS,
        "message": f"{len(candidates)} review item(s) re-opened with a {DEMO_SLA_SECONDS // 60}-minute SLA window.",
    }
