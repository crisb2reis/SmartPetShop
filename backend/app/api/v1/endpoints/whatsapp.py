import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import whatsapp_service
from app.agents.chatbot_agent import chatbot_agent
from app.schemas.whatsapp import (
    WhatsAppMessageResponse,
    WebhookProcessingResult,
    WhatsAppTestAgentRequest,
    WhatsAppTestAgentResponse
)

router = APIRouter()
logger = logging.getLogger("smartpetshop.whatsapp.api")


@router.get(
    "/webhook",
    summary="Validação de Webhook da Meta (Hub Challenge)",
    description="Endpoint exigido pela Meta Cloud API para validar o webhook via hub.mode, hub.verify_token e retornar o hub.challenge em texto puro."
)
@router.get(
    "/webhook/",
    include_in_schema=False
)
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Verificação de Webhook da Meta Cloud API.
    A Meta envia: GET /webhook?hub.mode=subscribe&hub.challenge=1158201444&hub.verify_token=meu_token
    Retorna o challenge diretamente como texto com status 200.
    """
    challenge = whatsapp_service.verify_webhook_token(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge
    )

    if challenge is not None:
        # A Meta exige resposta em formato texto simples (não JSON)
        return PlainTextResponse(content=str(challenge), status_code=status.HTTP_200_OK)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verificação de webhook recusada. Token ou modo inválidos."
    )


@router.post(
    "/webhook",
    response_model=WebhookProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="Receber eventos e mensagens da Meta Cloud API",
    description="Captura mensagens recebidas (texto, áudio, mídia) e atualizações de status enviadas pelo WhatsApp."
)
@router.post(
    "/webhook/",
    response_model=WebhookProcessingResult,
    include_in_schema=False
)
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe o payload de eventos da Meta.
    Valida a assinatura HMAC X-Hub-Signature-256 e grava a mensagem na tabela de auditoria com garantia de idempotência.
    """
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # 1. Validação de segurança criptográfica
    if not whatsapp_service.verify_meta_signature(body_bytes, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura X-Hub-Signature-256 inválida."
        )

    # 2. Parse do JSON recebido
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"[WhatsApp Webhook] Payload JSON inválido: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload JSON malformado."
        )

    # 3. Processamento de idempotência e gravação na tabela whatsapp_messages
    result = await whatsapp_service.process_meta_webhook(db, payload)

    return WebhookProcessingResult(
        status=result.get("status", "ok"),
        messages_processed=result.get("messages_processed", 0),
        statuses_processed=result.get("statuses_processed", 0),
        duplicate_messages_skipped=result.get("duplicate_messages_skipped", 0),
        details=result.get("details", [])
    )


@router.get(
    "/messages",
    response_model=List[WhatsAppMessageResponse],
    summary="Listar histórico de mensagens do WhatsApp",
    description="Retorna as mensagens auditadas trocadas via WhatsApp, com filtro opcional por telefone."
)
@router.get(
    "/messages/",
    include_in_schema=False
)
async def list_messages(
    phone: Optional[str] = Query(None, description="Filtrar por número de telefone"),
    limit: int = Query(50, ge=1, le=100, description="Limite de registros"),
    skip: int = Query(0, ge=0, description="Offset de registros"),
    db: AsyncSession = Depends(get_db)
):
    return await whatsapp_service.list_whatsapp_messages(
        db,
        phone=phone,
        limit=limit,
        skip=skip
    )


@router.post(
    "/process-message",
    response_model=WhatsAppTestAgentResponse,
    summary="Processar mensagem com o Agente de IA do WhatsApp",
    description="Executa o motor conversacional Rex 🐾 para mensagens do WhatsApp com histórico de contexto e Tool Calling."
)
async def process_whatsapp_message(
    payload: WhatsAppTestAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await chatbot_agent.process_whatsapp_message(
        db=db,
        from_phone=payload.phone,
        user_text=payload.message
    )
    return WhatsAppTestAgentResponse(
        session_id=result["session_id"],
        reply=result.get("reply"),
        tools_called=result.get("tools_called", []),
        handoff_requested=result.get("handoff_requested", False),
        status=result.get("status", "active")
    )

