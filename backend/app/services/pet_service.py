import uuid
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pet import Pet
from app.schemas.pet import PetCreate, PetUpdate


async def get_pet(db: AsyncSession, pet_id: uuid.UUID) -> Optional[Pet]:
    query = select(Pet).where(Pet.id == pet_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_pets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    tutor_id: Optional[uuid.UUID] = None,
    species: Optional[str] = None,
    search: Optional[str] = None
) -> List[Pet]:
    query = select(Pet)
    if tutor_id:
        query = query.where(Pet.tutor_id == tutor_id)
    if species:
        query = query.where(Pet.species.ilike(species))
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Pet.name.ilike(search_filter),
                Pet.breed.ilike(search_filter)
            )
        )
    query = query.order_by(Pet.name.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_pet(db: AsyncSession, pet_in: PetCreate) -> Pet:
    pet = Pet(
        tutor_id=pet_in.tutor_id,
        name=pet_in.name,
        species=pet_in.species,
        breed=pet_in.breed,
        birth_date=pet_in.birth_date,
        weight=pet_in.weight,
        gender=pet_in.gender,
        color=pet_in.color,
        photo_url=pet_in.photo_url,
        medical_notes=pet_in.medical_notes
    )
    db.add(pet)
    await db.flush()
    await db.refresh(pet)
    return pet


async def update_pet(db: AsyncSession, pet: Pet, pet_in: PetUpdate) -> Pet:
    update_data = pet_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(pet, field, val)
    db.add(pet)
    await db.flush()
    await db.refresh(pet)
    return pet


async def delete_pet(db: AsyncSession, pet: Pet) -> None:
    await db.delete(pet)
    await db.flush()

