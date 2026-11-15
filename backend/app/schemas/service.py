import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nome do serviço (ex: Banho e Tosa Completa)")
    category: str = Field(..., min_length=2, max_length=50, description="Categoria: Banho, Tosa, Veterinário, Vacinação")
    description: Optional[str] = Field(None, description="Descrição detalhada do serviço")
    price: Decimal = Field(..., ge=0.0, decimal_places=2, description="Preço do serviço")
    duration_minutes: int = Field(60, ge=15, le=480, description="Duração estimada em minutos")
    active: bool = Field(True, description="Se o serviço está ativo para novos agendamentos")


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0.0, decimal_places=2)
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
