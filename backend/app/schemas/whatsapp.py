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


class SendTextMessageRequest(BaseModel):
    phone: str = Field(..., description="Telefone do destinatário em formato E.164 (ex: 5511999998888)")
    text: str = Field(..., min_length=1, description="Texto da mensagem (suporta formatação WhatsApp: *negrito*, listas)")


class QuickReplyButton(BaseModel):
    id: str = Field(..., description="Identificador único da ação do botão")
    title: str = Field(..., max_length=20, description="Título do botão (máximo 20 caracteres)")


class SendInteractiveButtonsRequest(BaseModel):
    phone: str = Field(..., description="Telefone do destinatário em formato E.164")
    body_text: str = Field(..., description="Texto principal da mensagem")
    buttons: List[QuickReplyButton] = Field(..., min_length=1, max_length=3, description="Lista de 1 a 3 botões interativos")
    header_text: Optional[str] = Field(None, description="Cabeçalho opcional da mensagem")
    footer_text: Optional[str] = Field("SmartPetShop 🐾", description="Rodapé opcional da mensagem")


class SendTemplateRequest(BaseModel):
    phone: str = Field(..., description="Telefone do destinatário em formato E.164")
    template_name: str = Field(..., description="Nome do template HSM aprovado na Meta")
    language_code: str = Field("pt_BR", description="Código do idioma (ex: pt_BR)")
    parameters: List[str] = Field(default=[], description="Parâmetros posicionais de texto para o corpo do template")


class SendVaccineReminderRequest(BaseModel):
    phone: str = Field(..., description="Telefone do tutor")
    pet_name: str = Field(..., description="Nome do pet")
    vaccine_name: str = Field(..., description="Nome da vacina (ex: V10, Antirrábica)")
    due_date: str = Field(..., description="Data de vencimento do reforço (DD/MM/AAAA)")
    alert_type: str = Field("vaccine_d7", description="Tipo do alerta: vaccine_d30, vaccine_d7, vaccine_d0, vaccine_overdue")


class SendMessageResult(BaseModel):
    success: bool
    message_id: str
    status: str
    recipient: str
    mode: str = "simulation" # meta_api ou simulation
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class WebhookAsyncQueuedResponse(BaseModel):
    status: str = "queued"
    message: str = "Payload enfileirado para processamento assíncrono com sucesso."
    job_id: str
    created_at: str


class QueueStatusResponse(BaseModel):
    is_running: bool
    broker: str
    redis_connected: bool
    in_memory_queue_size: int
    total_processed: int
    total_failed: int
    total_retried: int
    stored_jobs_count: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    attempts: int
    max_retries: int
    created_at: str
    updated_at: str
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None




