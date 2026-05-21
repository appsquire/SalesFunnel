from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EnrollmentApplication
from app.validation_errors import EnrollmentValidationError
from app.schemas import EnrollmentCreate, EnrollmentPatch, EnrollmentResponse
from app.services.enrollment import (
    create_enrollment,
    enrollment_to_response,
    patch_enrollment,
    submit_enrollment,
)
from app.services.email import send_application_received
from app.settings import settings

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentResponse)
def post_enrollment(body: EnrollmentCreate, db: Session = Depends(get_db)) -> dict:
    if body.step != 1:
        raise HTTPException(status_code=400, detail="POST creates draft at step 1 (contact) only")
    try:
        row = create_enrollment(db, body.step, body.payload)
    except EnrollmentValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": e.message, "field_errors": e.field_errors},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": str(e), "field_errors": {}},
        ) from e
    return enrollment_to_response(row)


@router.get("/{draft_uuid}", response_model=EnrollmentResponse)
def get_enrollment(draft_uuid: str, db: Session = Depends(get_db)) -> dict:
    row = db.query(EnrollmentApplication).filter(EnrollmentApplication.draft_uuid == draft_uuid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    return enrollment_to_response(row)


@router.patch("/{draft_uuid}", response_model=EnrollmentResponse)
def patch_enrollment_route(draft_uuid: str, body: EnrollmentPatch, db: Session = Depends(get_db)) -> dict:
    row = db.query(EnrollmentApplication).filter(EnrollmentApplication.draft_uuid == draft_uuid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        row = patch_enrollment(
            db,
            row,
            step=body.step,
            payload=body.payload,
            current_step=body.current_step,
            max_step_reached=body.max_step_reached,
            step_status=body.step_status,
        )
    except EnrollmentValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": e.message, "field_errors": e.field_errors},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": str(e), "field_errors": {}},
        ) from e
    return enrollment_to_response(row)


@router.post("/{draft_uuid}/submit", response_model=EnrollmentResponse)
def submit(draft_uuid: str, db: Session = Depends(get_db)) -> dict:
    row = db.query(EnrollmentApplication).filter(EnrollmentApplication.draft_uuid == draft_uuid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    row = submit_enrollment(db, row)
    payload = enrollment_to_response(row)
    p = payload["payload"]
    msg_id = send_application_received(
        to_email=p.get("email", ""),
        to_name=p.get("first_name", ""),
        reference_number=row.reference_number or "",
        upload_url=f"{settings.public_app_url}/enroll/upload/pending",
    )
    if msg_id:
        row.mailgun_message_id = msg_id
        db.commit()
    return payload
