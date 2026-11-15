import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Nome da empresa/pet shop (ex: Pet Shop Patas & Pelos)")
    cnpj: Optional[str] = Field(None, max_length=20, description="CNPJ da empresa")
    plan: str = Field("pro", description="starter, pro, enterprise")


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegisterAdmin(BaseModel):
    """Cadastro inicial de nova empresa e seu usuário Administrador."""
    organization_name: str = Field(..., min_length=2, max_length=150)
    organization_cnpj: Optional[str] = None
    admin_name: str = Field(..., min_length=2, max_length=150)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6, max_length=100)


class UserCreate(BaseModel):
    """Cadastro de novo funcionário pela empresa."""
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field("receptionist", pattern="^(admin|receptionist|veterinarian|groomer)$", description="Perfil RBAC")


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    email: str
    role: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    name: str
    organization_name: str

