import json
import re
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator

from app.funnel_config import load_funnel_config
from app.validation_errors import EnrollmentValidationError, validation_error_from_pydantic


class Step1Contact(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    primary_phone: str = Field(min_length=7, max_length=20)

    @field_validator("primary_phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10:
            raise ValueError("Phone number must include at least 10 digits")
        return digits


class EnrollmentCreate(BaseModel):
    step: int = 1
    payload: dict[str, Any]


class EnrollmentPatch(BaseModel):
    step: int = Field(ge=0, le=11)
    payload: dict[str, Any] = Field(default_factory=dict)
    current_step: int | None = None
    max_step_reached: int | None = None
    step_status: dict[str, str] | None = None


class EnrollmentResponse(BaseModel):
    draft_uuid: str
    status: str
    current_step: int
    max_step_reached: int
    step_status: dict[str, str]
    payload: dict[str, Any]
    reference_number: str | None = None

    model_config = {"from_attributes": True}


def validate_step_payload(step: int, payload: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **payload}
    if step == 1:
        try:
            contact = Step1Contact(
                first_name=merged.get("first_name") or "",
                last_name=merged.get("last_name") or "",
                email=merged.get("email") or "",
                primary_phone=merged.get("primary_phone") or "",
            )
        except ValidationError as exc:
            raise validation_error_from_pydantic(exc) from exc
        return {**merged, **contact.model_dump(), "email": str(contact.email)}
    if step == 2:
        birthday = merged.get("birthday")
        if not birthday:
            raise EnrollmentValidationError(
                {"birthday": "Birthday is required."},
                message="Birthday is required.",
            )
    if step == 3:
        if not merged.get("applicant_type"):
            raise EnrollmentValidationError(
                {"applicant_type": "Select whether you are the customer or an authorized representative."},
                message="Applicant type is required.",
            )
        if merged.get("applicant_type") == "authorized_representative":
            if not merged.get("authorized_rep_details"):
                raise EnrollmentValidationError(
                    {"authorized_rep_details": "Authorized representative details are required."},
                    message="Complete authorized representative information.",
                )
            if not merged.get("authorized_rep_pad_day"):
                raise EnrollmentValidationError(
                    {"authorized_rep_pad_day": "Select a PAD withdrawal day."},
                    message="PAD withdrawal day is required for authorized representatives.",
                )
    if step == 4:
        cfg = load_funnel_config()
        min_days = cfg.get("branding", {}).get("service_date_min_days", 10)
        svc = merged.get("requested_service_date")
        if not svc:
            raise EnrollmentValidationError(
                {"requested_service_date": "Requested service date is required."},
                message="Service date is required.",
            )
        moving = merged.get("moving_new_location")
        if moving not in ("yes", "no"):
            raise EnrollmentValidationError(
                {"moving_new_location": "Please indicate if you are moving to a new location."},
                message="Moving question is required.",
            )
        svc_date = date.fromisoformat(svc) if isinstance(svc, str) else svc
        if svc_date < date.today() + timedelta(days=min_days):
            raise EnrollmentValidationError(
                {"requested_service_date": f"Choose a date at least {min_days} days from today."},
                message="Requested service date is too soon.",
            )
    if step == 5:
        if merged.get("location_has_power") not in ("yes", "no"):
            raise EnrollmentValidationError(
                {"location_has_power": "Please indicate if the location currently has power."},
                message="This field is required.",
            )
        if merged.get("location_has_power") == "no" and merged.get("want_power_at_site") not in ("yes", "no"):
            raise EnrollmentValidationError(
                {"want_power_at_site": "Please indicate if you want power at this site."},
                message="Required when location has no power.",
            )
    if step == 6:
        if merged.get("green_power") not in ("yes", "no"):
            raise EnrollmentValidationError(
                {"green_power": "Please indicate if you want green power."},
                message="Green power question is required.",
            )
        if merged.get("green_power") == "yes" and merged.get("green_percentage") in (None, ""):
            raise EnrollmentValidationError(
                {"green_percentage": "Select a green power percentage."},
                message="Green percentage is required.",
            )
        merged = compute_green_costs(merged)
        return merged
    if step == 7:
        for key, label in (
            ("billing_street", "Street address"),
            ("billing_city", "City"),
            ("billing_postal", "Postal code"),
        ):
            if not merged.get(key):
                raise EnrollmentValidationError(
                    {key: f"{label} is required."},
                    message="Billing address is incomplete.",
                )
    if step == 8:
        if merged.get("service_same_as_billing") == "yes":
            merged = {
                **merged,
                "service_street": merged.get("billing_street"),
                "service_city": merged.get("billing_city"),
                "service_postal": merged.get("billing_postal"),
            }
        else:
            for key, label in (
                ("service_street", "Service street"),
                ("service_city", "Service city"),
                ("service_postal", "Service postal code"),
            ):
                if not merged.get(key):
                    raise EnrollmentValidationError(
                        {key: f"{label} is required."},
                        message="Service location is incomplete.",
                    )
    if step == 10:
        if merged.get("disclosure_acknowledged") != "yes" or merged.get("pad_acknowledged") != "yes":
            raise EnrollmentValidationError(
                {
                    "disclosure_acknowledged": "You must accept the agreements to continue.",
                },
                message="Please accept the agreements.",
            )
    return merged


def compute_green_costs(payload: dict[str, Any]) -> dict[str, Any]:
    cfg = load_funnel_config()
    charge = float(cfg.get("branding", {}).get("green_charge_per_kwh", 0.0185))
    pct = float(payload.get("green_percentage") or 0)
    kwh = float(payload.get("example_kwh_per_month") or 600)
    if not payload.get("green_power"):
        return payload
    green_kwh_year = kwh * 12 * (pct / 100)
    cost_year = green_kwh_year * charge
    cost_month = cost_year / 12
    cost_day_cents = round((cost_year / 365) * 100)
    return {
        **payload,
        "green_cost_per_year": round(cost_year, 2),
        "green_cost_per_month": round(cost_month, 2),
        "green_cost_per_day_cents": int(cost_day_cents),
    }
