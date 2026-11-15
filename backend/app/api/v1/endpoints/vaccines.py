import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import vaccine_service, pet_service
from app.schemas.vaccine import (
    VaccineCatalogResponse,
    VaccineBatchResponse,
    PetVaccinationRecordCreate,
    PetVaccinationRecordUpdate,
    PetVaccinationRecordResponse,
    PetVaccinationCardResponse
)

router = APIRouter()


# -------------------------------------------------------------
# 1. Catálogo Oficial de Vacinas
# -------------------------------------------------------------
@router.get(
    "/vaccine-catalogs/",
    response_model=List[VaccineCatalogResponse],
    summary="Listar catálogo oficial de vacinas",
    description="Retorna as vacinas pré-cadastradas no sistema, com opção de filtro por espécie (CANINO, FELINO, AMBOS)."
)
async def list_vaccine_catalogs(
    species: Optional[str] = Query(None, description="Filtro por espécie: CANINO, FELINO ou AMBOS"),
    db: AsyncSession = Depends(get_db)
):
    return await vaccine_service.get_vaccine_catalogs(db, species=species)


# -------------------------------------------------------------
# 2. Lotes de Vacinas (Estoque e Rastreabilidade)
# -------------------------------------------------------------
@router.get(
    "/vaccine-batches/",
    response_model=List[VaccineBatchResponse],
    summary="Listar lotes ativos de vacinas",
    description="Retorna os lotes de vacina ativos em estoque para seleção no ato da aplicação."
)
async def list_vaccine_batches(
    catalog_id: Optional[uuid.UUID] = Query(None, description="Filtrar por vacina do catálogo"),
    db: AsyncSession = Depends(get_db)
):
    return await vaccine_service.get_active_batches(db, catalog_id=catalog_id)


# -------------------------------------------------------------
# 3. Carteirinha de Vacinação do Pet
# -------------------------------------------------------------
@router.get(
    "/pets/{pet_id}/vaccinations/",
    response_model=List[PetVaccinationRecordResponse],
    summary="Listar histórico de vacinação do pet",
    description="Retorna o extrato completo de vacinas aplicadas e pendentes do pet."
)
async def list_pet_vaccinations(
    pet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )
    return await vaccine_service.get_pet_vaccination_records(db, pet_id)


@router.get(
    "/pets/{pet_id}/vaccinations/card",
    response_model=PetVaccinationCardResponse,
    summary="Extrato da Carteirinha Digital do Pet",
    description="Retorna a carteirinha digital formatada com contadores de doses em dia, próximas e atrasadas."
)
async def get_pet_vaccination_card(
    pet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )
    return await vaccine_service.get_pet_vaccination_card(db, pet)


@router.post(
    "/pets/{pet_id}/vaccinations/",
    response_model=PetVaccinationRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar aplicação de vacina",
    description="Registra uma nova dose de vacina para o pet, validando lote, CRMV e calculando o reforço automaticamente."
)
async def create_pet_vaccination(
    pet_id: uuid.UUID,
    record_in: PetVaccinationRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validar existência do pet
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )

    # 2. Validar vacina no catálogo oficial
    catalog = await vaccine_service.get_vaccine_catalog_by_id(db, record_in.vaccine_catalog_id)
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacina não encontrada no catálogo oficial."
        )

    # 3. Validar lote se fornecido
    batch = None
    if record_in.vaccine_batch_id:
        batch = await vaccine_service.get_batch_by_id(db, record_in.vaccine_batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lote de vacina informado não foi encontrado."
            )
        if batch.expiration_date < record_in.application_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é permitido aplicar vacina de lote vencido. Validade do lote: {batch.expiration_date.strftime('%d/%m/%Y')}."
            )

    return await vaccine_service.create_pet_vaccination(
        db=db,
        pet=pet,
        data=record_in,
        catalog=catalog,
        batch=batch
    )


@router.put(
    "/pets/{pet_id}/vaccinations/{record_id}",
    response_model=PetVaccinationRecordResponse,
    summary="Atualizar registro de vacina",
    description="Atualiza um lançamento de vacina (correção de data, CRMV, lote ou status)."
)
async def update_pet_vaccination(
    pet_id: uuid.UUID,
    record_id: uuid.UUID,
    record_in: PetVaccinationRecordUpdate,
    db: AsyncSession = Depends(get_db)
):
    record = await vaccine_service.get_vaccination_record_by_id(db, record_id)
    if not record or record.pet_id != pet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de vacinação não encontrado para este pet."
        )

    catalog = None
    if record_in.vaccine_catalog_id:
        catalog = await vaccine_service.get_vaccine_catalog_by_id(db, record_in.vaccine_catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacina não encontrada no catálogo."
            )

    return await vaccine_service.update_pet_vaccination(
        db=db,
        record=record,
        data=record_in,
        catalog=catalog
    )
