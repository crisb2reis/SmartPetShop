import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_roles
)
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    UserRegisterAdmin,
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    OrganizationResponse
)

router = APIRouter()


@router.post(
    "/register-company",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo Pet Shop (Multi-tenant Onboarding)",
    description="Cria uma nova empresa/pet shop e cadastra o usuário Administrador com isolamento de dados garantido."
)
async def register_company(
    reg_in: UserRegisterAdmin,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar se e-mail já existe
    query = select(User).where(User.email == reg_in.admin_email)
    existing_user = await db.execute(query)
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado no sistema."
        )

    # 2. Criar Organização / Pet Shop
    org = Organization(
        name=reg_in.organization_name,
        cnpj=reg_in.organization_cnpj,
        plan="pro",
        active=True
    )
    db.add(org)
    await db.flush()

    # 3. Criar Usuário Administrador vinculado ao tenant
    admin_user = User(
        tenant_id=org.id,
        name=reg_in.admin_name,
        email=reg_in.admin_email,
        hashed_password=hash_password(reg_in.admin_password),
        role="admin",
        active=True
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    token = create_access_token(
        user_id=admin_user.id,
        tenant_id=org.id,
        role=admin_user.role,
        name=admin_user.name
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=admin_user.id,
        tenant_id=org.id,
        role=admin_user.role,
        name=admin_user.name,
        organization_name=org.name
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de funcionário",
    description="Autentica um funcionário de qualquer pet shop e retorna seu token de acesso com escopo de tenant e perfil."
)
async def login(
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(User).options(selectinload(User.organization)).where(User.email == login_in.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado. Contate o administrador do pet shop."
        )

    if not user.organization.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso suspenso para este pet shop."
        )

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        name=user.name
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        name=user.name,
        organization_name=user.organization.name
    )


@router.get(
    "/me",
    summary="Perfil do usuário conectado",
    description="Retorna dados do funcionário autenticado e da empresa a qual pertence."
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "organization": {
            "id": current_user.organization.id,
            "name": current_user.organization.name,
            "cnpj": current_user.organization.cnpj,
            "plan": current_user.organization.plan
        }
    }


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar funcionário (Exclusivo Admin)",
    description="Permite que o Administrador de um pet shop crie contas para sua equipe (recepção, veterinários, tosadores)."
)
async def create_employee(
    user_in: UserCreate,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db)
):
    # Verifica se e-mail já existe
    query = select(User).where(User.email == user_in.email)
    res = await db.execute(query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este e-mail no sistema."
        )

    # Cria funcionário OBRIGATORIAMENTE no mesmo tenant_id do administrador
    new_user = User(
        tenant_id=current_user.tenant_id,
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="Listar funcionários da empresa (Exclusivo Admin)",
    description="Retorna a equipe cadastrada no pet shop do administrador logado."
)
async def list_employees(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db)
):
    # Filtro automático pelo tenant do usuário logado (Petshop A jamais vê Petshop B)
    query = select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.name.asc())
    res = await db.execute(query)
    return list(res.scalars().all())

