import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EnrollmentApplication(Base):
    __tablename__ = "enrollment_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    max_step_reached: Mapped[int] = mapped_column(Integer, default=0)
    step_status_json: Mapped[str] = mapped_column(Text, default="{}")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    reference_number: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    mailgun_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
