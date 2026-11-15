from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.pet import Pet
    from app.models.alert import Alert
    from app.models.chat import ChatSession


class Tutor(TimestampedModel):
    __tablename__ = "tutors"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    pets: Mapped[List["Pet"]] = relationship("Pet", back_populates="tutor", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="tutor", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="tutor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tutor id={self.id} name='{self.name}' phone='{self.phone}'>"

