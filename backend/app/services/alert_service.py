import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
from app.schemas.alert import AlertCreate


async def get_alert(
    db: AsyncSession,
    alert_id: uuid.UUID,
    load_relations: bool = True
) -> Optional[Alert]:
    query = select(Alert).where(Alert.id == alert_id)
    if load_relations:
        query = query.options(selectinload(Alert.pet), selectinload(Alert.tutor))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_alerts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    tutor_id: Optional[uuid.UUID] = None,
    pet_id: Optional[uuid.UUID] = None,
    alert_type: Optional[str] = None
) -> List[Alert]:
    query = select(Alert).options(selectinload(Alert.pet), selectinload(Alert.tutor))
    conditions = []

    if status:
        conditions.append(Alert.status == status)
    if tutor_id:
        conditions.append(Alert.tutor_id == tutor_id)
    if pet_id:
        conditions.append(Alert.pet_id == pet_id)
    if alert_type:
        conditions.append(Alert.alert_type == alert_type)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Alert.scheduled_for.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def has_recent_alert(
    db: AsyncSession,
    pet_id: uuid.UUID,
    alert_type: str,
    days: int = 7
) -> bool:
    """Verifica se já existe alerta similar gerado para o pet nos últimos X dias."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = select(Alert).where(
        and_(
            Alert.pet_id == pet_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= cutoff
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def create_alert(db: AsyncSession, alert_in: AlertCreate) -> Alert:
    alert = Alert(
        tutor_id=alert_in.tutor_id,
        pet_id=alert_in.pet_id,
        alert_type=alert_in.alert_type,
        message=alert_in.message,
        status=alert_in.status,
        scheduled_for=alert_in.scheduled_for,
        sent_at=alert_in.sent_at
    )
    db.add(alert)
    await db.flush()
    return await get_alert(db, alert.id, load_relations=True)


async def update_alert_status(db: AsyncSession, alert: Alert, new_status: str) -> Alert:
    alert.status = new_status
    if new_status == "sent" and not alert.sent_at:
        alert.sent_at = datetime.utcnow()
    db.add(alert)
    await db.flush()
    return await get_alert(db, alert.id, load_relations=True)
