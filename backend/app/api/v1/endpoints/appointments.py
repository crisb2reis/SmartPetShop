import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AvailableSlotsResponse
)
from app.services import appointment_service, pet_service, service_service

router = APIRouter()


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo agendamento",
    description="Registra um agendamento para um pet. Valida existência de conflitos de horário com antecedência."
)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validar pet
    pet = await pet_service.get_pet(db, appointment_in.pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )

    # 2. Validar serviço
    service = await service_service.get_service(db, appointment_in.service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )
    if not service.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este serviço está atualmente inativo para novos agendamentos."
        )

    # 3. Validar conflito de agenda
    has_conflict = await appointment_service.check_conflicts(
        db,
        service_id=appointment_in.service_id,
        scheduled_at=appointment_in.scheduled_at
    )
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de horário! Já existe outro atendimento agendado para este intervalo de tempo."
        )

    return await appointment_service.create_appointment(db, appointment_in)


@router.get(
    "/",
    response_model=List[AppointmentResponse],
    summary="Listar agendamentos",
    description="Retorna lista de agendamentos com filtros opcionais por data, pet, serviço ou status."
)
async def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    target_date: Optional[date] = Query(None, description="Filtrar por data específica (YYYY-MM-DD)"),
    pet_id: Optional[uuid.UUID] = Query(None, description="Filtrar por pet"),
    service_id: Optional[uuid.UUID] = Query(None, description="Filtrar por serviço"),
    status: Optional[str] = Query(None, description="Filtrar por status: scheduled, in_progress, completed, canceled"),
    db: AsyncSession = Depends(get_db)
):
    return await appointment_service.list_appointments(
        db,
        skip=skip,
        limit=limit,
        target_date=target_date,
        pet_id=pet_id,
        service_id=service_id,
        status=status
    )


@router.get(
    "/availability",
    response_model=AvailableSlotsResponse,
    summary="Consultar horários disponíveis",
    description="Calcula e retorna os horários livres na agenda para determinado serviço e data. Ideal para uso pelo Chatbot IA."
)
async def check_availability(
    service_id: uuid.UUID = Query(..., description="ID do serviço desejado"),
    target_date: date = Query(..., description="Data para consulta (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    service = await service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )

    slots = await appointment_service.get_available_slots(db, service, target_date)
    return AvailableSlotsResponse(
        target_date=target_date,
        service_name=service.name,
        duration_minutes=service.duration_minutes,
        slots=slots
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Buscar agendamento por ID",
    description="Retorna detalhes completos do agendamento, incluindo os dados do pet e do serviço."
)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    appointment = await appointment_service.get_appointment(db, appointment_id, load_relations=True)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado."
        )
    return appointment


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Atualizar agendamento",
    description="Atualiza data/hora, serviço, status ou observações de um agendamento."
)
async def update_appointment(
    appointment_id: uuid.UUID,
    appointment_in: AppointmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    appointment = await appointment_service.get_appointment(db, appointment_id, load_relations=False)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado."
        )

    # Se alterou data ou serviço, verificar conflito
    if appointment_in.scheduled_at or appointment_in.service_id:
        target_service_id = appointment_in.service_id or appointment.service_id
        target_time = appointment_in.scheduled_at or appointment.scheduled_at

        has_conflict = await appointment_service.check_conflicts(
            db,
            service_id=target_service_id,
            scheduled_at=target_time,
            exclude_id=appointment.id
        )
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflito de horário! O novo horário solicitado já está ocupado."
            )

    return await appointment_service.update_appointment(db, appointment, appointment_in)


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancelar agendamento",
    description="Muda o status do agendamento para 'canceled' liberando o horário para outros pets."
)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    appointment = await appointment_service.get_appointment(db, appointment_id, load_relations=False)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado."
        )
    return await appointment_service.cancel_appointment(db, appointment)
