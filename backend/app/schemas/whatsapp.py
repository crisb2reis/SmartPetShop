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
