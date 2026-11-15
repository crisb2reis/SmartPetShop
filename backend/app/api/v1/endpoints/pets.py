import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.pet import PetCreate, PetUpdate, PetResponse
from app.services import pet_service, tutor_service

router = APIRouter()


@router.post(
    "/",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo pet",
    description="Cadastra um novo animal vinculado a um tutor existente."
)
async def create_pet(
    pet_in: PetCreate,
    db: AsyncSession = Depends(get_db)
):
    tutor = await tutor_service.get_tutor(db, pet_in.tutor_id)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor proprietário não encontrado."
        )
    return await pet_service.create_pet(db, pet_in)


@router.get(
    "/",
    response_model=List[PetResponse],
    summary="Listar pets",
    description="Retorna lista de pets com filtros opcionais por tutor, espécie ou busca por nome/raça."
)
async def list_pets(
    skip: int = Query(0, ge=0, description="Offset de registros"),
    limit: int = Query(50, ge=1, le=100, description="Limite por página"),
    tutor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por tutor"),
    species: Optional[str] = Query(None, description="Filtrar por espécie (ex: canino, felino)"),
    search: Optional[str] = Query(None, description="Buscar por nome ou raça"),
    db: AsyncSession = Depends(get_db)
):
    return await pet_service.list_pets(
        db,
        skip=skip,
        limit=limit,
        tutor_id=tutor_id,
        species=species,
        search=search
    )


@router.get(
    "/{pet_id}",
    response_model=PetResponse,
    summary="Buscar pet por ID",
    description="Obtém os detalhes cadastrais e médicos de um pet específico."
)
async def get_pet(
    pet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )
    return pet


@router.put(
    "/{pet_id}",
    response_model=PetResponse,
    summary="Atualizar pet",
    description="Atualiza os dados de um pet existente."
)
async def update_pet(
    pet_id: uuid.UUID,
    pet_in: PetUpdate,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )

    if pet_in.tutor_id and pet_in.tutor_id != pet.tutor_id:
        tutor = await tutor_service.get_tutor(db, pet_in.tutor_id)
        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Novo tutor informado não foi encontrado."
            )

    return await pet_service.update_pet(db, pet, pet_in)


@router.delete(
    "/{pet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover pet",
    description="Exclui o pet e seus agendamentos/histórico associados."
)
async def delete_pet(
    pet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    pet = await pet_service.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado."
        )
    await pet_service.delete_pet(db, pet)
    return None

