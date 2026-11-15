import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.pet import PetResponse
from app.schemas.tutor import TutorResponse


class AlertBase(BaseModel):
    tutor_id: uuid.UUID = Field(..., description="ID do tutor que receberá a notificação")
    pet_id: uuid.UUID = Field(..., description="ID do pet alvo do alerta")
    alert_type: str = Field(..., description="Tipo do alerta: vaccine_due, dewormer_due, bath_recurrence, checkup_suggested")
    message: str = Field(..., min_length=5, description="Mensagem personalizada gerada para o tutor")
    status: str = Field("pending", pattern="^(pending|sent|clicked|dismissed)$", description="Status do alerta")
    scheduled_for: datetime = Field(..., description="Data/hora prevista para o envio da mensagem")
    sent_at: Optional[datetime] = Field(None, description="Data/hora efetiva em que foi enviado")


class AlertCreate(AlertBase):
    pass


class AlertUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(pending|sent|clicked|dismissed)$")


class AlertResponse(AlertBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    pet: Optional[PetResponse] = None
    tutor: Optional[TutorResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AlertScanResult(BaseModel):
    total_pets_analyzed: int
    alerts_generated: int
    alerts: List[AlertResponse]
