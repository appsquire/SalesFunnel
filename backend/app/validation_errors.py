from pydantic import ValidationError


class EnrollmentValidationError(Exception):
    """User-facing step validation with per-field messages."""

    def __init__(
        self,
        field_errors: dict[str, str],
        message: str = "Please fix the errors below.",
    ) -> None:
        self.field_errors = field_errors
        self.message = message
        super().__init__(message)


_FIELD_LABELS: dict[str, str] = {
    "first_name": "First name",
    "last_name": "Last name",
    "email": "Email",
    "primary_phone": "Phone",
    "birthday": "Birthday",
    "requested_service_date": "Requested service date",
}


def _humanize_pydantic_error(err: dict) -> str:
    err_type = err.get("type", "")
    ctx = err.get("ctx") or {}

    if err_type == "string_too_short":
        min_len = ctx.get("min_length", 1)
        if min_len >= 1:
            return "This field is required."
        return "Value is too short."
    if err_type == "string_too_long":
        return "Value is too long."
    if err_type in ("value_error", "value_error.missing"):
        msg = err.get("msg", "")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        return msg or "Invalid value."
    if "email" in err_type or err_type == "value_error":
        msg = str(err.get("msg", ""))
        if "@" in msg or "email" in msg.lower():
            return "Enter a valid email address."
    if err_type == "missing":
        return "This field is required."
    # Pydantic custom ValueError from validators
    msg = err.get("msg")
    if isinstance(msg, str):
        if msg.startswith("Value error, "):
            return msg[len("Value error, ") :]
        return msg
    return "Invalid value."


def pydantic_validation_to_field_errors(exc: ValidationError) -> dict[str, str]:
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc", ())
        # Skip wrapper model name (e.g. Step1Contact)
        parts = [p for p in loc if p != "Step1Contact" and isinstance(p, str)]
        if not parts:
            continue
        field = parts[-1]
        if field not in field_errors:
            field_errors[field] = _humanize_pydantic_error(err)
    return field_errors


def validation_error_from_pydantic(exc: ValidationError) -> EnrollmentValidationError:
    field_errors = pydantic_validation_to_field_errors(exc)
    if not field_errors:
        return EnrollmentValidationError({}, "Please check your entries and try again.")
    if len(field_errors) == 1:
        label = _FIELD_LABELS.get(next(iter(field_errors)), "A field")
        return EnrollmentValidationError(field_errors, f"{label} needs attention.")
    return EnrollmentValidationError(
        field_errors,
        f"Please complete {len(field_errors)} required fields.",
    )
