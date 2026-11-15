import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.tutor import TutorCreate, TutorUpdate, TutorResponse, TutorWithPetsResponse
from app.schemas.pet import PetResponse
from app.services import tutor_service, pet_service

router = APIRouter()


@router.post(
    "/",
    response_model=TutorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo tutor",
    description="Cadastra um novo tutor de pet. O telefone/WhatsApp deve ser único."
)
async def create_tutor(
    tutor_in: TutorCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_phone = await tutor_service.get_tutor_by_phone(db, tutor_in.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um tutor cadastrado com este telefone."
        )

    if tutor_in.email:
        existing_email = await tutor_service.get_tutor_by_email(db, tutor_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um tutor cadastrado com este e-mail."
            )

    return await tutor_service.create_tutor(db, tutor_in)


@router.get(
    "/",
    response_model=List[TutorResponse],
    summary="Listar tutores",
    description="Retorna lista paginada de tutores, com opção de busca por nome, telefone ou e-mail."
)
async def list_tutors(
    skip: int = Query(0, ge=0, description="Offset de registros"),
    limit: int = Query(50, ge=1, le=100, description="Limite por página"),
    search: Optional[str] = Query(None, description="Termo para busca"),
    db: AsyncSession = Depends(get_db)
):
    return await tutor_service.list_tutors(db, skip=skip, limit=limit, search=search)


@router.get(
    "/{tutor_id}",
    response_model=TutorWithPetsResponse,
    summary="Buscar tutor por ID",
    description="Obtém os detalhes de um tutor incluindo a lista de seus pets."
)
async def get_tutor(
    tutor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    tutor = await tutor_service.get_tutor(db, tutor_id, load_pets=True)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor não encontrado."
        )
    return tutor


@router.put(
    "/{tutor_id}",
    response_model=TutorResponse,
    summary="Atualizar tutor",
    description="Atualiza os dados cadastrais do tutor."
)
async def update_tutor(
    tutor_id: uuid.UUID,
    tutor_in: TutorUpdate,
    db: AsyncSession = Depends(get_db)
):
    tutor = await tutor_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor não encontrado."
        )

    if tutor_in.phone and tutor_in.phone != tutor.phone:
        existing = await tutor_service.get_tutor_by_phone(db, tutor_in.phone)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O novo telefone informado já pertence a outro tutor."
            )

    return await tutor_service.update_tutor(db, tutor, tutor_in)


@router.delete(
    "/{tutor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover tutor",
    description="Exclui o tutor e seus dados associados (pets, alertas, histórico)."
)
async def delete_tutor(
    tutor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    tutor = await tutor_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor não encontrado."
        )
    await tutor_service.delete_tutor(db, tutor)
    return None


@router.get(
    "/{tutor_id}/pets",
    response_model=List[PetResponse],
    summary="Listar pets do tutor",
    description="Retorna todos os pets vinculados a este tutor."
)
async def list_tutor_pets(
    tutor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    tutor = await tutor_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor não encontrado."
        )
    return await pet_service.list_pets(db, tutor_id=tutor_id)

