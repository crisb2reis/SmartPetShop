import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.tutor import Tutor
    from app.models.pet import Pet


class Alert(TimestampedModel):
    __tablename__ = "alerts"

    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # vaccine_due, dewormer_due, bath_recurrence, checkup_suggested
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True
    )  # pending, sent, clicked, dismissed
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="alerts")
    pet: Mapped["Pet"] = relationship("Pet", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} type='{self.alert_type}' status='{self.status}'>"
