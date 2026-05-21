import logging

from app.settings import settings

logger = logging.getLogger(__name__)


def send_application_received(*, to_email: str, to_name: str, reference_number: str, upload_url: str | None) -> str | None:
    if settings.mail_driver == "log":
        logger.info(
            "MAIL (log driver) to=%s name=%s ref=%s upload=%s",
            to_email,
            to_name,
            reference_number,
            upload_url,
        )
        return "log-stub-message-id"
    # Mailgun integration placeholder for production
    logger.warning("Mailgun not configured; set MAIL_DRIVER=mailgun and API keys")
    return None
