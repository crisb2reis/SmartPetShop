import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthRecordBase(BaseModel):
    pet_id: uuid.UUID = Field(..., description="ID do pet")
    record_type: str = Field(..., min_length=2, max_length=50, description="Tipo: vaccine, dewormer, exam, medication, surgery")
    title: str = Field(..., min_length=2, max_length=150, description="Nome da vacina, remédio ou procedimento (ex: Vacina V10, Giardíase)")
    application_date: date = Field(..., description="Data em que foi aplicado/realizado")
    next_due_date: Optional[date] = Field(None, description="Data prevista para a próxima dose / reforço")
    veterinarian_name: Optional[str] = Field(None, max_length=150, description="Nome do médico veterinário responsável")
    batch_number: Optional[str] = Field(None, max_length=100, description="Número de lote da vacina ou medicamento")
    notes: Optional[str] = Field(None, description="Reações adversas ou observações clínicas")


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordUpdate(BaseModel):
    record_type: Optional[str] = Field(None, min_length=2, max_length=50)
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    application_date: Optional[date] = None
    next_due_date: Optional[date] = None
    veterinarian_name: Optional[str] = None
    batch_number: Optional[str] = None
    notes: Optional[str] = None


class HealthRecordResponse(HealthRecordBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
