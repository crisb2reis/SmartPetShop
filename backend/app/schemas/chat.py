import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    session_id: Optional[uuid.UUID] = Field(None, description="ID da sessão de chat existente (opcional para nova conversa)")
    tutor_id: Optional[uuid.UUID] = Field(None, description="ID do tutor (se autenticado)")
    channel: str = Field("web", description="Canal de origem: web, whatsapp, telegram")
    content: str = Field(..., min_length=1, description="Texto da mensagem enviada pelo usuário")


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    metadata_info: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    tutor_id: Optional[uuid.UUID] = None
    channel: str
    status: str
    created_at: datetime
    messages: List[ChatMessageOut] = []

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    reply: str
    tools_called: List[Dict[str, Any]] = []
    created_at: datetime
