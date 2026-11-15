import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class WhatsAppMessageResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    message_id: str
    phone: str
    direction: str
    message_type: str
    content: Optional[str] = None
    status: str
    tutor_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookProcessingResult(BaseModel):
    status: str = "ok"
    messages_processed: int = 0
    statuses_processed: int = 0
    duplicate_messages_skipped: int = 0
    details: Optional[List[Dict[str, Any]]] = None


class WhatsAppTestAgentRequest(BaseModel):
    phone: str = Field(..., description="Telefone do cliente (ex: 11987654321)")
    message: str = Field(..., description="Texto da mensagem enviada pelo cliente no WhatsApp")


class WhatsAppTestAgentResponse(BaseModel):
    session_id: str
    reply: Optional[str] = None
    tools_called: List[Dict[str, Any]] = []
    handoff_requested: bool = False
    status: str


