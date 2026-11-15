import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.tutor import Tutor


class ChatSession(TimestampedModel):
    __tablename__ = "chat_sessions"

    tutor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    channel: Mapped[str] = mapped_column(String(50), default="web", nullable=False) # web, whatsapp, telegram
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False) # active, closed

    # Relacionamentos
    tutor: Mapped["Tutor | None"] = relationship("Tutor", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(TimestampedModel):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False) # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # Tool calls, function responses

    # Relacionamentos
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
