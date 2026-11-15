import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.pet import PetResponse


class TutorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Nome completo do tutor")
    phone: str = Field(..., min_length=8, max_length=30, description="Telefone de contato/WhatsApp")
    email: Optional[EmailStr] = Field(None, description="E-mail de contato")
    address: Optional[str] = Field(None, description="Endereço residencial completo")
    notes: Optional[str] = Field(None, description="Preferências de contato ou observações gerais")


class TutorCreate(TutorBase):
    pass


class TutorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = Field(None, min_length=8, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class TutorResponse(TutorBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorWithPetsResponse(TutorResponse):
    pets: List[PetResponse] = []

    model_config = ConfigDict(from_attributes=True)
