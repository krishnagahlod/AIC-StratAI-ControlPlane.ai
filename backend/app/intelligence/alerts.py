import datetime

from app.db.models import Alert, utcnow

_DEDUP_WINDOW = datetime.timedelta(hours=1)
_SEVERITY_BY_RISK = {"critical": "critical", "moderate": "medium", "low": "low", "minimal": "info"}


def register(db, app_id: int, interaction_id: int, risk_level: str, flags: list[dict]) -> Alert | None:
    if not flags:
        return None

    lead = max(flags, key=lambda f: {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(f["severity"], 0))
    severity = "critical" if lead["severity"] == "critical" else _SEVERITY_BY_RISK.get(risk_level, "medium")
    dedup_key = f"{app_id}:{lead['type']}"
    now = utcnow()

    existing = (
        db.query(Alert)
        .filter(Alert.dedup_key == dedup_key, Alert.updated_at > now - _DEDUP_WINDOW)
        .order_by(Alert.updated_at.desc())
        .first()
    )
    if existing:
        existing.count += 1
        existing.updated_at = now
        existing.severity = severity
        existing.interaction_id = interaction_id
        existing.message = f"{lead['detail']} (seen {existing.count}x in the last hour)"
        return existing

    alert = Alert(
        severity=severity,
        dedup_key=dedup_key,
        count=1,
        message=lead["detail"],
        app_id=app_id,
        interaction_id=interaction_id,
    )
    db.add(alert)
    return alert
