import json
import logging
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import whatsapp_service
from app.services.whatsapp_queue import whatsapp_queue
from app.agents.chatbot_agent import chatbot_agent
from app.schemas.whatsapp import (
    WhatsAppMessageResponse,
    WebhookProcessingResult,
    WebhookAsyncQueuedResponse,
    QueueStatusResponse,
    JobStatusResponse,
    WhatsAppTestAgentRequest,
    WhatsAppTestAgentResponse,
    SendTextMessageRequest,
    SendInteractiveButtonsRequest,
    SendTemplateRequest,
    SendVaccineReminderRequest,
    SendMessageResult
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
    response_model=Union[WebhookAsyncQueuedResponse, WebhookProcessingResult],
    status_code=status.HTTP_200_OK,
    summary="Receber eventos e mensagens da Meta Cloud API (Processamento Assíncrono)",
    description="Captura eventos da Meta, valida assinatura HMAC e enfileira imediatamente em background para resposta ultra-rápida (< 100ms)."
)
@router.post(
    "/webhook/",
    response_model=Union[WebhookAsyncQueuedResponse, WebhookProcessingResult],
    include_in_schema=False
)
async def receive_webhook(
    request: Request,
    sync: bool = Query(False, description="Se True, executa síncrono. Padrão False (processamento assíncrono via Fila/Worker)."),
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe o payload de eventos da Meta Cloud API.
    1. Valida a assinatura HMAC X-Hub-Signature-256 (SHA-256).
    2. Em modo assíncrono (padrão): Enfileira o payload bruto na fila (Redis / Worker) e responde HTTP 200 imediatamente para a Meta.
    3. O worker em background processa idempotência, executa o Agente de IA e despacha a resposta ao cliente.
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

    # 3. Processamento síncrono (opcional para testes específicos)
    if sync:
        result = await whatsapp_service.process_meta_webhook(db, payload)
        return WebhookProcessingResult(
            status=result.get("status", "ok"),
            messages_processed=result.get("messages_processed", 0),
            statuses_processed=result.get("statuses_processed", 0),
            duplicate_messages_skipped=result.get("duplicate_messages_skipped", 0),
            details=result.get("details", [])
        )

    # 4. Processamento Assíncrono via Fila e Worker (Meta Standard < 1s)
    job = await whatsapp_queue.enqueue(payload)
    return WebhookAsyncQueuedResponse(
        status="queued",
        message="Payload enfileirado para processamento assíncrono com sucesso.",
        job_id=job.job_id,
        created_at=job.created_at
    )


@router.get(
    "/queue/status",
    response_model=QueueStatusResponse,
    summary="Status da fila e worker assíncrono do WhatsApp",
    description="Retorna métricas operacionais da fila de processamento (broker ativo, tamanho da fila, tarefas concluídas e falhas)."
)
async def get_queue_status():
    return whatsapp_queue.get_stats()


@router.get(
    "/queue/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Consultar status de um job enfileirado",
    description="Retorna o status, tentativas, timestamp e resultado da execução de um job assíncrono."
)
async def get_job_status(job_id: str):
    job = whatsapp_queue.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado."
        )
    return job


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


# ============================================================================
# Endpoints de Envio de Mensagens (Outbound via Meta Cloud API)
# ============================================================================

@router.post(
    "/send-text",
    response_model=SendMessageResult,
    summary="Enviar mensagem de texto no WhatsApp",
    description="Dispara mensagem de texto simples ou formatada para o cliente via Meta Cloud API."
)
async def send_text(
    payload: SendTextMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await whatsapp_service.send_text_message(
        db=db,
        phone=payload.phone,
        text=payload.text
    )
    return SendMessageResult(**res)


@router.post(
    "/send-interactive",
    response_model=SendMessageResult,
    summary="Enviar mensagem com botões interativos no WhatsApp",
    description="Dispara mensagem com até 3 botões rápidos de ação (Quick Replies) via Meta Cloud API."
)
async def send_interactive(
    payload: SendInteractiveButtonsRequest,
    db: AsyncSession = Depends(get_db)
):
    buttons_dict = [{"id": b.id, "title": b.title} for b in payload.buttons]
    res = await whatsapp_service.send_interactive_buttons(
        db=db,
        phone=payload.phone,
        body_text=payload.body_text,
        buttons=buttons_dict,
        header_text=payload.header_text,
        footer_text=payload.footer_text
    )
    return SendMessageResult(**res)


@router.post(
    "/send-template",
    response_model=SendMessageResult,
    summary="Enviar template oficial HSM aprovado na Meta",
    description="Dispara mensagem baseada em template aprovado fora da janela de atendimento de 24h."
)
async def send_template(
    payload: SendTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await whatsapp_service.send_template_message(
        db=db,
        phone=payload.phone,
        template_name=payload.template_name,
        language_code=payload.language_code,
        parameters=payload.parameters
    )
    return SendMessageResult(**res)


@router.post(
    "/send-vaccine-reminder",
    response_model=SendMessageResult,
    summary="Disparar alerta oficial de reforço de vacina no WhatsApp",
    description="Dispara notificação de vacina a vencer ou atrasada com botões interativos para agendamento imediato."
)
async def send_vaccine_reminder(
    payload: SendVaccineReminderRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await whatsapp_service.send_vaccine_reminder_message(
        db=db,
        phone=payload.phone,
        pet_name=payload.pet_name,
        vaccine_name=payload.vaccine_name,
        due_date=payload.due_date,
        alert_type=payload.alert_type
    )
    return SendMessageResult(**res)

