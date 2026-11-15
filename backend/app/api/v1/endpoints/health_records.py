import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.health_record import (
    HealthRecordCreate,
    HealthRecordUpdate,
    HealthRecordResponse
)
from app.services import health_record_service, pet_service

router = APIRouter()


@router.post(
    "/",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar histórico de saúde/vacina",
    description="Registra vacinas aplicadas, vermífugos, exames ou medicações com data prevista para reforço."
)
async def create_health_record(
    record_in: HealthRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, record_in.pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )
    return await health_record_service.create_health_record(db, record_in)


@router.get(
    "/",
    response_model=List[HealthRecordResponse],
    summary="Listar registros de saúde",
    description="Consulta o prontuário médico dos pets, com filtros por pet e tipo de registro."
)
async def list_health_records(
    pet_id: Optional[uuid.UUID] = Query(None, description="Filtrar por pet específico"),
    record_type: Optional[str] = Query(None, description="Filtrar por tipo (vaccine, dewormer, exam, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    return await health_record_service.list_health_records(
        db,
        pet_id=pet_id,
        record_type=record_type
    )


@router.get(
    "/{record_id}",
    response_model=HealthRecordResponse,
    summary="Buscar registro de saúde por ID"
)
async def get_health_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    record = await health_record_service.get_health_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado."
        )
    return record


@router.put(
    "/{record_id}",
    response_model=HealthRecordResponse,
    summary="Atualizar registro de saúde"
)
async def update_health_record(
    record_id: uuid.UUID,
    record_in: HealthRecordUpdate,
    db: AsyncSession = Depends(get_db)
):
    record = await health_record_service.get_health_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado."
        )
    return await health_record_service.update_health_record(db, record, record_in)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir registro de saúde"
)
async def delete_health_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    record = await health_record_service.get_health_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado."
        )
    await health_record_service.delete_health_record(db, record)
    return None

