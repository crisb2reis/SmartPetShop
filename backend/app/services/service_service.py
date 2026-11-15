import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


async def get_service(db: AsyncSession, service_id: uuid.UUID) -> Optional[Service]:
    query = select(Service).where(Service.id == service_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_service_by_name(db: AsyncSession, name: str) -> Optional[Service]:
    query = select(Service).where(Service.name.ilike(name))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_services(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    active_only: bool = True
) -> List[Service]:
    query = select(Service)
    if active_only:
        query = query.where(Service.active.is_(True))
    if category:
        query = query.where(Service.category.ilike(category))
    query = query.order_by(Service.category.asc(), Service.name.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_service(db: AsyncSession, service_in: ServiceCreate) -> Service:
    service = Service(
        name=service_in.name,
        category=service_in.category,
        description=service_in.description,
        price=service_in.price,
        duration_minutes=service_in.duration_minutes,
        active=service_in.active
    )
    db.add(service)
    await db.flush()
    await db.refresh(service)
    return service


async def update_service(db: AsyncSession, service: Service, service_in: ServiceUpdate) -> Service:
    update_data = service_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(service, field, val)
    db.add(service)
    await db.flush()
    await db.refresh(service)
    return service


async def delete_service(db: AsyncSession, service: Service) -> None:
    await db.delete(service)
    await db.flush()

