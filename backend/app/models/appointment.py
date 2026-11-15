import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.pet import Pet
    from app.models.service import Service


class Appointment(TimestampedModel):
    __tablename__ = "appointments"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="scheduled",
        nullable=False,
        index=True
    )  # scheduled, in_progress, completed, canceled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    pet: Mapped["Pet"] = relationship("Pet", back_populates="appointments")
    service: Mapped["Service"] = relationship("Service", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} scheduled_at={self.scheduled_at} status='{self.status}'>"

