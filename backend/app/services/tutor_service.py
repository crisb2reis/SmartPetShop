import uuid
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tutor import Tutor
from app.schemas.tutor import TutorCreate, TutorUpdate


async def get_tutor(db: AsyncSession, tutor_id: uuid.UUID, load_pets: bool = False) -> Optional[Tutor]:
    query = select(Tutor).where(Tutor.id == tutor_id)
    if load_pets:
        query = query.options(selectinload(Tutor.pets))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tutor_by_phone(db: AsyncSession, phone: str) -> Optional[Tutor]:
    query = select(Tutor).where(Tutor.phone == phone)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tutor_by_email(db: AsyncSession, email: str) -> Optional[Tutor]:
    query = select(Tutor).where(Tutor.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_tutors(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[Tutor]:
    query = select(Tutor)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Tutor.name.ilike(search_filter),
                Tutor.phone.ilike(search_filter),
                Tutor.email.ilike(search_filter)
            )
        )
    query = query.order_by(Tutor.name.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_tutor(db: AsyncSession, tutor_in: TutorCreate) -> Tutor:
    tutor = Tutor(
        name=tutor_in.name,
        phone=tutor_in.phone,
        email=tutor_in.email,
        address=tutor_in.address,
        notes=tutor_in.notes
    )
    db.add(tutor)
    await db.flush()
    await db.refresh(tutor)
    return tutor


async def update_tutor(db: AsyncSession, tutor: Tutor, tutor_in: TutorUpdate) -> Tutor:
    update_data = tutor_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(tutor, field, val)
    db.add(tutor)
    await db.flush()
    await db.refresh(tutor)
    return tutor


async def delete_tutor(db: AsyncSession, tutor: Tutor) -> None:
    await db.delete(tutor)
    await db.flush()
