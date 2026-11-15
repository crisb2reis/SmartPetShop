import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.pet import PetResponse
from app.schemas.service import ServiceResponse


class AppointmentBase(BaseModel):
    pet_id: uuid.UUID = Field(..., description="ID do pet a ser atendido")
    service_id: uuid.UUID = Field(..., description="ID do serviço a ser realizado")
    scheduled_at: datetime = Field(..., description="Data e hora do agendamento (ISO 8601)")
    notes: Optional[str] = Field(None, description="Observações ou instruções específicas")


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    service_id: Optional[uuid.UUID] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|in_progress|completed|canceled)$")
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    pet: Optional[PetResponse] = None
    service: Optional[ServiceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotsQuery(BaseModel):
    service_id: uuid.UUID
    target_date: date


class AvailableSlotsResponse(BaseModel):
    target_date: date
    service_name: str
    duration_minutes: int
    slots: List[str]
