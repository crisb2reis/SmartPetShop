import os
import hmac
import hashlib
import json
import base64
import time
import uuid
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization

security_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "smartpetshop_super_secret_jwt_key_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400  # 24 horas


# -------------------------------------------------------------
# 1. Hashing Seguro de Senhas (PBKDF2-HMAC-SHA256 + Salt)
# -------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt + key).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        decoded = base64.b64decode(hashed_password.encode("ascii"))
        salt = decoded[:16]
        stored_key = decoded[16:]
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(stored_key, new_key)
    except Exception:
        return False


# -------------------------------------------------------------
# 2. Emissão e Validação de Tokens JWT (HMAC-SHA256 Zero-Dep)
# -------------------------------------------------------------
def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_access_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str,
    name: str,
    expires_in: int = JWT_EXPIRATION_SECONDS
) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "name": name,
        "iat": now,
        "exp": now + expires_in
    }

    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}".encode("ascii")

    signature = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token JWT malformado")

        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()

        if not hmac.compare_digest(_b64_encode(expected_sig), sig_b64):
            raise ValueError("Assinatura do token inválida")

        payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token expirado")

        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciais inválidas ou sessão expirada: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -------------------------------------------------------------
# 3. Injeção de Dependência de Usuário e Tenant Atual
# -------------------------------------------------------------
async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not auth_credentials or not auth_credentials.credentials:
        # Modo de desenvolvimento sem autenticação ou requisição não-autenticada
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária. Envie o token Bearer.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(auth_credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem identificação de usuário")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID de usuário inválido")

    query = select(User).options(selectinload(User.organization)).where(User.id == user_uuid)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inexistente ou desativado")

    if not user.organization or not user.organization.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Empresa desativada ou com acesso suspenso")

    return user


# -------------------------------------------------------------
# 4. Controle de Acesso Baseado em Funções (RBAC)
# -------------------------------------------------------------
def require_roles(*allowed_roles: str):
    """
    Filtro RBAC que valida se o usuário possui um dos papéis autorizados.
    Exemplo de uso: Depends(require_roles('admin', 'receptionist'))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Ação restrita a perfis: {', '.join(allowed_roles)}. Seu perfil é '{current_user.role}'."
            )
        return current_user

    return role_checker

