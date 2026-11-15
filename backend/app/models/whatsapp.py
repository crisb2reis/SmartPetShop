import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.tutor import Tutor


class WhatsAppMessage(TimestampedModel):
    """
    Tabela de auditoria, histórico e idempotência de mensagens do WhatsApp Business (Meta Cloud API).
    Armazena mensagens recebidas (INBOUND) e enviadas (OUTBOUND), com rastreamento de status e payload bruto.
    """
    __tablename__ = "whatsapp_messages"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )  # ID exclusivo da mensagem gerado pela Meta (ex: wamid.HBgM...) para garantia de idempotência
    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # Telefone do contato em formato E.164 (ex: 5511999998888)
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INBOUND",
        index=True
    )  # INBOUND (recebida do cliente), OUTBOUND (enviada pelo pet shop/IA)
    message_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="text"
    )  # text, audio, image, interactive, button, template, document
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )  # Conteúdo textual da mensagem, texto do botão ou transcrição de áudio
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="received",
        index=True
    )  # received, processing, sent, delivered, read, failed
    tutor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # Tutor associado automaticamente pelo número de telefone
    raw_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )  # Payload JSON bruto recebido ou enviado via Meta Graph API

    # Relacionamentos
    organization: Mapped["Organization"] = relationship("Organization")
    tutor: Mapped[Optional["Tutor"]] = relationship("Tutor")

    def __repr__(self) -> str:
        return f"<WhatsAppMessage id={self.id} msg_id='{self.message_id}' phone='{self.phone}' dir='{self.direction}'>"
