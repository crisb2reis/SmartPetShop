import uuid
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vaccine import VaccineCatalog, VaccineBatch, PetVaccinationRecord
from app.models.pet import Pet
from app.schemas.vaccine import (
    PetVaccinationRecordCreate,
    PetVaccinationRecordUpdate,
    PetVaccinationCardResponse
)


async def get_vaccine_catalogs(
    db: AsyncSession,
    species: Optional[str] = None
) -> List[VaccineCatalog]:
    query = select(VaccineCatalog)
    if species:
        species_upper = species.upper()
        query = query.where(
            or_(
                VaccineCatalog.species == species_upper,
                VaccineCatalog.species == "AMBOS"
            )
        )
    query = query.order_by(VaccineCatalog.species, VaccineCatalog.name)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_vaccine_catalog_by_id(
    db: AsyncSession,
    catalog_id: uuid.UUID
) -> Optional[VaccineCatalog]:
    query = select(VaccineCatalog).where(VaccineCatalog.id == catalog_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_active_batches(
    db: AsyncSession,
    catalog_id: Optional[uuid.UUID] = None,
    tenant_id: Optional[uuid.UUID] = None
) -> List[VaccineBatch]:
    query = select(VaccineBatch).where(VaccineBatch.active.is_(True))
    if catalog_id:
        query = query.where(VaccineBatch.vaccine_catalog_id == catalog_id)
    if tenant_id:
        query = query.where(VaccineBatch.tenant_id == tenant_id)
    query = query.order_by(VaccineBatch.expiration_date.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_batch_by_id(
    db: AsyncSession,
    batch_id: uuid.UUID
) -> Optional[VaccineBatch]:
    query = select(VaccineBatch).where(VaccineBatch.id == batch_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_pet_vaccination_records(
    db: AsyncSession,
    pet_id: uuid.UUID
) -> List[PetVaccinationRecord]:
    query = (
        select(PetVaccinationRecord)
        .where(PetVaccinationRecord.pet_id == pet_id)
        .options(
            selectinload(PetVaccinationRecord.vaccine_catalog),
            selectinload(PetVaccinationRecord.vaccine_batch)
        )
        .order_by(PetVaccinationRecord.application_date.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_vaccination_record_by_id(
    db: AsyncSession,
    record_id: uuid.UUID
) -> Optional[PetVaccinationRecord]:
    query = (
        select(PetVaccinationRecord)
        .where(PetVaccinationRecord.id == record_id)
        .options(
            selectinload(PetVaccinationRecord.vaccine_catalog),
            selectinload(PetVaccinationRecord.vaccine_batch)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_pet_vaccination(
    db: AsyncSession,
    pet: Pet,
    data: PetVaccinationRecordCreate,
    catalog: VaccineCatalog,
    batch: Optional[VaccineBatch] = None,
    tenant_id: Optional[uuid.UUID] = None
) -> PetVaccinationRecord:
    # Cálculo automático de next_due_date se não informada pelo usuário
    next_due = data.next_due_date
    if not next_due:
        booster_days = catalog.booster_interval_days or 365
        next_due = data.application_date + timedelta(days=booster_days)

    # Determina o status com base na data de vencimento
    status_val = data.status
    today = date.today()
    if next_due and next_due < today:
        status_val = "ATRASADA"
    elif status_val == "APLICADA" and next_due and (next_due - today).days <= 30:
        # Próxima do vencimento
        pass

    record = PetVaccinationRecord(
        tenant_id=tenant_id or pet.tenant_id,
        pet_id=pet.id,
        vaccine_catalog_id=catalog.id,
        vaccine_batch_id=batch.id if batch else None,
        application_date=data.application_date,
        next_due_date=next_due,
        vet_name=data.vet_name,
        vet_crmv=data.vet_crmv,
        clinic_id=tenant_id or pet.tenant_id,
        status=status_val,
        notes=data.notes
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # Recarrega relacionamentos
    return await get_vaccination_record_by_id(db, record.id) # type: ignore


async def update_pet_vaccination(
    db: AsyncSession,
    record: PetVaccinationRecord,
    data: PetVaccinationRecordUpdate,
    catalog: Optional[VaccineCatalog] = None
) -> PetVaccinationRecord:
    if data.vaccine_catalog_id is not None:
        record.vaccine_catalog_id = data.vaccine_catalog_id
    if data.vaccine_batch_id is not None:
        record.vaccine_batch_id = data.vaccine_batch_id
    if data.application_date is not None:
        record.application_date = data.application_date
    if data.vet_name is not None:
        record.vet_name = data.vet_name
    if data.vet_crmv is not None:
        record.vet_crmv = data.vet_crmv
    if data.notes is not None:
        record.notes = data.notes

    if data.next_due_date is not None:
        record.next_due_date = data.next_due_date
    elif data.application_date is not None and catalog:
        record.next_due_date = data.application_date + timedelta(days=catalog.booster_interval_days or 365)

    if data.status is not None:
        record.status = data.status
    elif record.next_due_date and record.next_due_date < date.today():
        record.status = "ATRASADA"

    await db.commit()
    await db.refresh(record)
    return await get_vaccination_record_by_id(db, record.id) # type: ignore


async def get_pet_vaccination_card(
    db: AsyncSession,
    pet: Pet
) -> dict:
    records = await get_pet_vaccination_records(db, pet.id)
    today = date.today()

    applied = []
    upcoming = []
    due_soon_count = 0
    overdue_count = 0

    for r in records:
        if r.status == "APLICADA":
            applied.append(r)
        
        # Avalia vencimento
        if r.next_due_date:
            days_diff = (r.next_due_date - today).days
            if days_diff < 0:
                overdue_count += 1
                upcoming.append(r)
            elif days_diff <= 30:
                due_soon_count += 1
                upcoming.append(r)

    return {
        "pet_id": pet.id,
        "pet_name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "total_applied": len(applied),
        "due_soon_count": due_soon_count,
        "overdue_count": overdue_count,
        "applied_records": applied,
        "upcoming_records": upcoming,
        "all_records": records
    }

