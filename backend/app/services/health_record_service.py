import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.health_record import HealthRecord
from app.schemas.health_record import HealthRecordCreate, HealthRecordUpdate


async def get_health_record(db: AsyncSession, record_id: uuid.UUID) -> Optional[HealthRecord]:
    query = select(HealthRecord).where(HealthRecord.id == record_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_health_records(
    db: AsyncSession,
    pet_id: Optional[uuid.UUID] = None,
    record_type: Optional[str] = None
) -> List[HealthRecord]:
    query = select(HealthRecord)
    if pet_id:
        query = query.where(HealthRecord.pet_id == pet_id)
    if record_type:
        query = query.where(HealthRecord.record_type.ilike(record_type))
    query = query.order_by(HealthRecord.application_date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_health_record(db: AsyncSession, record_in: HealthRecordCreate) -> HealthRecord:
    record = HealthRecord(
        pet_id=record_in.pet_id,
        record_type=record_in.record_type,
        title=record_in.title,
        application_date=record_in.application_date,
        next_due_date=record_in.next_due_date,
        veterinarian_name=record_in.veterinarian_name,
        batch_number=record_in.batch_number,
        notes=record_in.notes
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def update_health_record(
    db: AsyncSession,
    record: HealthRecord,
    record_in: HealthRecordUpdate
) -> HealthRecord:
    update_data = record_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(record, field, val)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def delete_health_record(db: AsyncSession, record: HealthRecord) -> None:
    await db.delete(record)
    await db.flush()

