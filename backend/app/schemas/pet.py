import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome do pet")
    species: str = Field(..., min_length=1, max_length=50, description="Espécie: canino, felino, ave, etc.")
    breed: Optional[str] = Field(None, max_length=100, description="Raça ou SRD")
    birth_date: Optional[date] = Field(None, description="Data de nascimento aproximada")
    weight: Optional[float] = Field(None, ge=0.0, le=150.0, description="Peso em kg")
    gender: Optional[str] = Field(None, max_length=10, description="Macho ou Fêmea")
    color: Optional[str] = Field(None, max_length=50, description="Cor predominante")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL da foto")
    medical_notes: Optional[str] = Field(None, description="Alergias, observações médicas ou de temperamento")


class PetCreate(PetBase):
    tutor_id: uuid.UUID = Field(..., description="ID do tutor proprietário")


class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[str] = Field(None, min_length=1, max_length=50)
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    weight: Optional[float] = Field(None, ge=0.0, le=150.0)
    gender: Optional[str] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    medical_notes: Optional[str] = None
    tutor_id: Optional[uuid.UUID] = None


class PetResponse(PetBase):
    id: uuid.UUID
    tutor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
