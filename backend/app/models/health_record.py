import uuid
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import String, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.pet import Pet


class HealthRecord(TimestampedModel):
    __tablename__ = "health_records"

    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    record_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # vaccine, dewormer, exam, medication, surgery
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    application_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True) # Prazo de reforço / validade
    veterinarian_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)        # Lote da vacina/remédio
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    pet: Mapped["Pet"] = relationship("Pet", back_populates="health_records")

    def __repr__(self) -> str:
        return f"<HealthRecord id={self.id} type='{self.record_type}' title='{self.title}'>"
