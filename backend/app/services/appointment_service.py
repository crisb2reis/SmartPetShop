import uuid
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.service import Service
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


async def get_appointment(
    db: AsyncSession,
    appointment_id: uuid.UUID,
    load_relations: bool = True
) -> Optional[Appointment]:
    query = select(Appointment).where(Appointment.id == appointment_id)
    if load_relations:
        query = query.options(
            selectinload(Appointment.pet),
            selectinload(Appointment.service)
        )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_appointments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    target_date: Optional[date] = None,
    pet_id: Optional[uuid.UUID] = None,
    service_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None
) -> List[Appointment]:
    query = select(Appointment).options(
        selectinload(Appointment.pet),
        selectinload(Appointment.service)
    )

    conditions = []
    if target_date:
        start_day = datetime.combine(target_date, time.min)
        end_day = datetime.combine(target_date, time.max)
        conditions.append(and_(Appointment.scheduled_at >= start_day, Appointment.scheduled_at <= end_day))

    if pet_id:
        conditions.append(Appointment.pet_id == pet_id)
    if service_id:
        conditions.append(Appointment.service_id == service_id)
    if status:
        conditions.append(Appointment.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Appointment.scheduled_at.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def check_conflicts(
    db: AsyncSession,
    service_id: uuid.UUID,
    scheduled_at: datetime,
    exclude_id: Optional[uuid.UUID] = None
) -> bool:
    """Verifica se há conflito de agendamento no mesmo horário."""
    # Obter duração do serviço
    service_query = select(Service).where(Service.id == service_id)
    service_res = await db.execute(service_query)
    service = service_res.scalar_one_or_none()
    duration = service.duration_minutes if service else 60

    new_start = scheduled_at
    new_end = scheduled_at + timedelta(minutes=duration)

    # Buscar agendamentos ativos no mesmo dia
    day_start = datetime.combine(scheduled_at.date(), time.min)
    day_end = datetime.combine(scheduled_at.date(), time.max)

    query = select(Appointment).join(Service).where(
        and_(
            Appointment.scheduled_at >= day_start,
            Appointment.scheduled_at <= day_end,
            Appointment.status.in_(["scheduled", "in_progress"])
        )
    ).options(selectinload(Appointment.service))

    if exclude_id:
        query = query.where(Appointment.id != exclude_id)

    result = await db.execute(query)
    existing_appointments = result.scalars().all()

    for appt in existing_appointments:
        appt_start = appt.scheduled_at
        appt_duration = appt.service.duration_minutes if appt.service else 60
        appt_end = appt_start + timedelta(minutes=appt_duration)

        # Se houver sobreposição
        if (new_start < appt_end) and (new_end > appt_start):
            return True

    return False


async def get_available_slots(
    db: AsyncSession,
    service: Service,
    target_date: date
) -> List[str]:
    """Calcula horários disponíveis entre 08:00 e 18:00 para uma data e serviço."""
    duration = service.duration_minutes
    slot_interval = timedelta(minutes=duration)

    opening_time = datetime.combine(target_date, time(8, 0))
    closing_time = datetime.combine(target_date, time(18, 0))

    # Buscar agendamentos existentes no dia
    query = select(Appointment).join(Service).where(
        and_(
            Appointment.scheduled_at >= opening_time,
            Appointment.scheduled_at <= closing_time,
            Appointment.status.in_(["scheduled", "in_progress"])
        )
    ).options(selectinload(Appointment.service))

    result = await db.execute(query)
    busy_appointments = result.scalars().all()

    busy_ranges = []
    for appt in busy_appointments:
        dur = appt.service.duration_minutes if appt.service else 60
        busy_ranges.append((appt.scheduled_at, appt.scheduled_at + timedelta(minutes=dur)))

    available_slots: List[str] = []
    current_time = opening_time

    while current_time + slot_interval <= closing_time:
        slot_end = current_time + slot_interval
        is_free = True

        for busy_start, busy_end in busy_ranges:
            if (current_time < busy_end) and (slot_end > busy_start):
                is_free = False
                break

        if is_free:
            available_slots.append(current_time.strftime("%H:%M"))

        current_time += timedelta(minutes=30)  # Incremento de 30 minutos na grade

    return available_slots


async def create_appointment(db: AsyncSession, appointment_in: AppointmentCreate) -> Appointment:
    appointment = Appointment(
        pet_id=appointment_in.pet_id,
        service_id=appointment_in.service_id,
        scheduled_at=appointment_in.scheduled_at,
        status="scheduled",
        notes=appointment_in.notes
    )
    db.add(appointment)
    await db.flush()
    return await get_appointment(db, appointment.id, load_relations=True)


async def update_appointment(
    db: AsyncSession,
    appointment: Appointment,
    appointment_in: AppointmentUpdate
) -> Appointment:
    update_data = appointment_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(appointment, field, val)
    db.add(appointment)
    await db.flush()
    return await get_appointment(db, appointment.id, load_relations=True)


async def cancel_appointment(db: AsyncSession, appointment: Appointment) -> Appointment:
    appointment.status = "canceled"
    db.add(appointment)
    await db.flush()
    return await get_appointment(db, appointment.id, load_relations=True)

