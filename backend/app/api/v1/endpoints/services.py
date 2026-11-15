import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services import service_service

router = APIRouter()


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo serviço",
    description="Cadastra um novo tipo de atendimento oferecido pelo pet shop (Banho, Tosa, Consulta, etc.)."
)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    existing = await service_service.get_service_by_name(db, service_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um serviço cadastrado com o nome '{service_in.name}'."
        )
    return await service_service.create_service(db, service_in)


@router.get(
    "/",
    response_model=List[ServiceResponse],
    summary="Listar catálogo de serviços",
    description="Retorna os serviços disponíveis com filtros por categoria e status ativo."
)
async def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filtrar por categoria (ex: Banho, Tosa, Veterinário)"),
    active_only: bool = Query(True, description="Listar apenas serviços ativos"),
    db: AsyncSession = Depends(get_db)
):
    return await service_service.list_services(
        db,
        skip=skip,
        limit=limit,
        category=category,
        active_only=active_only
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Buscar serviço por ID",
    description="Retorna os detalhes de um serviço específico."
)
async def get_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    service = await service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )
    return service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Atualizar serviço",
    description="Atualiza preço, duração estimada ou status de ativação do serviço."
)
async def update_service(
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = await service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )

    if service_in.name and service_in.name != service.name:
        existing = await service_service.get_service_by_name(db, service_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe outro serviço com o nome '{service_in.name}'."
            )

    return await service_service.update_service(db, service, service_in)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover serviço",
    description="Exclui o serviço do catálogo."
)
async def delete_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    service = await service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )
    await service_service.delete_service(db, service)
    return None

