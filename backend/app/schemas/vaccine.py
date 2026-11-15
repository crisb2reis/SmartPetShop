import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class VaccineCatalogBase(BaseModel):
    species: str = Field(..., description="CANINO, FELINO ou AMBOS")
    name: str = Field(..., min_length=2, max_length=150, description="Nome da vacina")
    type: str = Field("OBRIGATORIA", description="OBRIGATORIA ou OPCIONAL")
    recommended_age_weeks: int = Field(8, ge=0, description="Idade recomendada em semanas")
    doses_required: int = Field(1, ge=1, description="Doses no protocolo primário")
    booster_interval_days: int = Field(365, ge=1, description="Intervalo de reforço em dias")
    description: Optional[str] = Field(None, description="Descrição e indicações clínicas")


class VaccineCatalogCreate(VaccineCatalogBase):
    pass


class VaccineCatalogResponse(VaccineCatalogBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VaccineBatchBase(BaseModel):
    vaccine_catalog_id: uuid.UUID
    batch_number: str = Field(..., min_length=2, max_length=100)
    manufacturer: str = Field(..., min_length=2, max_length=150)
    expiration_date: date
    active: bool = True


class VaccineBatchCreate(VaccineBatchBase):
    pass


class VaccineBatchResponse(VaccineBatchBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    vaccine_catalog: Optional[VaccineCatalogResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PetVaccinationRecordBase(BaseModel):
    vaccine_catalog_id: uuid.UUID
    vaccine_batch_id: Optional[uuid.UUID] = None
    application_date: date = Field(default_factory=date.today)
    next_due_date: Optional[date] = None
    vet_name: str = Field(..., min_length=2, max_length=150, description="Nome do Médico Veterinário")
    vet_crmv: str = Field(..., min_length=2, max_length=50, description="CRMV/UF do profissional (ex: CRMV-SP 12345)")
    status: str = Field("APLICADA", description="APLICADA, PENDENTE ou ATRASADA")
    notes: Optional[str] = None


class PetVaccinationRecordCreate(PetVaccinationRecordBase):
    pass


class PetVaccinationRecordUpdate(BaseModel):
    vaccine_catalog_id: Optional[uuid.UUID] = None
    vaccine_batch_id: Optional[uuid.UUID] = None
    application_date: Optional[date] = None
    next_due_date: Optional[date] = None
    vet_name: Optional[str] = Field(None, min_length=2, max_length=150)
    vet_crmv: Optional[str] = Field(None, min_length=2, max_length=50)
    status: Optional[str] = None
    notes: Optional[str] = None


class PetVaccinationRecordResponse(PetVaccinationRecordBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    pet_id: uuid.UUID
    clinic_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    vaccine_catalog: Optional[VaccineCatalogResponse] = None
    vaccine_batch: Optional[VaccineBatchResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PetVaccinationCardResponse(BaseModel):
    pet_id: uuid.UUID
    pet_name: str
    species: str
    breed: Optional[str] = None
    total_applied: int
    due_soon_count: int
    overdue_count: int
    applied_records: List[PetVaccinationRecordResponse] = []
    upcoming_records: List[PetVaccinationRecordResponse] = []
    all_records: List[PetVaccinationRecordResponse] = []

    model_config = ConfigDict(from_attributes=True)

