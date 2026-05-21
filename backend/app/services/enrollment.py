import json
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import EnrollmentApplication
from app.schemas import compute_green_costs, validate_step_payload


def _loads(s: str) -> dict:
    return json.loads(s) if s else {}


def _dumps(d: dict) -> str:
    return json.dumps(d)


def enrollment_to_response(row: EnrollmentApplication) -> dict:
    return {
        "draft_uuid": row.draft_uuid,
        "status": row.status,
        "current_step": row.current_step,
        "max_step_reached": row.max_step_reached,
        "step_status": _loads(row.step_status_json),
        "payload": _loads(row.payload_json),
        "reference_number": row.reference_number,
    }


def create_enrollment(db: Session, step: int, payload: dict) -> EnrollmentApplication:
    validated = validate_step_payload(step, payload, {})
    if step >= 6:
        validated = compute_green_costs(validated)
    row = EnrollmentApplication(
        current_step=step,
        max_step_reached=step,
        step_status_json=_dumps({str(step): "complete"}),
        payload_json=_dumps(validated),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_enrollment(
    db: Session,
    row: EnrollmentApplication,
    *,
    step: int,
    payload: dict,
    current_step: int | None,
    max_step_reached: int | None,
    step_status: dict | None,
) -> EnrollmentApplication:
    if row.status != "draft":
        raise ValueError("Cannot modify a submitted application")
    existing = _loads(row.payload_json)
    validated = validate_step_payload(step, payload, existing)
    if step >= 6 or validated.get("green_power"):
        validated = compute_green_costs(validated)
    row.payload_json = _dumps(validated)
    row.current_step = current_step if current_step is not None else step
    row.max_step_reached = max(
        row.max_step_reached,
        max_step_reached if max_step_reached is not None else step,
    )
    if step_status is not None:
        row.step_status_json = _dumps(step_status)
    else:
        statuses = _loads(row.step_status_json)
        statuses[str(step)] = "complete"
        row.step_status_json = _dumps(statuses)
    db.commit()
    db.refresh(row)
    return row


def submit_enrollment(db: Session, row: EnrollmentApplication) -> EnrollmentApplication:
    if row.status == "submitted":
        return row
    ref = f"UN-{secrets.token_hex(4).upper()}"
    row.status = "submitted"
    row.reference_number = ref
    row.submitted_at = datetime.now(timezone.utc)
    row.current_step = 12
    db.commit()
    db.refresh(row)
    return row
