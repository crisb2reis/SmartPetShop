import uuid
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Date, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.tutor import Tutor
    from app.models.appointment import Appointment
    from app.models.health_record import HealthRecord
    from app.models.alert import Alert


class Pet(TimestampedModel):
    __tablename__ = "pets"

    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ex: canino, felino
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)         # ex: Golden Retriever, SRD
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)            # em kg
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)         # Macho, Fêmea
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)       # Alergias, cuidados especiais

    # Relacionamentos
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="pets")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="pet", cascade="all, delete-orphan")
    health_records: Mapped[List["HealthRecord"]] = relationship("HealthRecord", back_populates="pet", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="pet", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pet id={self.id} name='{self.name}' species='{self.species}'>"

