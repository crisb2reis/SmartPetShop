import hmac
import hashlib
import logging
import uuid
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.whatsapp import WhatsAppMessage
from app.models.tutor import Tutor
from app.models.organization import Organization

logger = logging.getLogger("smartpetshop.whatsapp")


def verify_meta_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Valida a assinatura criptográfica X-Hub-Signature-256 enviada pela Meta nos webhooks.
    Usa o WHATSAPP_APP_SECRET como chave secreta HMAC-SHA256.
    """
    if not settings.WHATSAPP_APP_SECRET:
        # Se não configurado secret em ambiente de desenvolvimento, aceita com log
        logger.debug("[WhatsApp] WHATSAPP_APP_SECRET não definido; pulando verificação de assinatura.")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("[WhatsApp] Cabeçalho X-Hub-Signature-256 ausente ou mal formatado.")
        return False

    expected_sig = signature_header.split("sha256=", 1)[1]
    computed_sig = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_sig, computed_sig)
    if not is_valid:
        logger.warning(f"[WhatsApp] Assinatura HMAC inválida. Esperada: {expected_sig}, Calculada: {computed_sig}")
    return is_valid


def verify_webhook_token(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
    """
    Valida a verificação inicial do Webhook exigida pela Meta (hub.mode, hub.verify_token).
    Retorna o challenge se o token conferir.
    """
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("[WhatsApp] Webhook verificado com sucesso pela Meta!")
        return challenge
    logger.warning(f"[WhatsApp] Falha na validação do webhook. Mode: {mode}, Token recebido: {token}")
    return None


async def get_message_by_meta_id(db: AsyncSession, message_id: str) -> Optional[WhatsAppMessage]:
    """Busca mensagem pelo ID único da Meta para garantir idempotência."""
    query = select(WhatsAppMessage).where(WhatsAppMessage.message_id == message_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def find_tutor_by_phone(db: AsyncSession, phone: str) -> Optional[Tutor]:
    """Tenta associar o número do WhatsApp ao cadastro de um tutor no banco de dados."""
    clean_phone = "".join(filter(str.isdigit, phone))
    # Ex: 5511999998888 -> tenta número completo ou últimos 9 dígitos
    patterns = [clean_phone]
    if len(clean_phone) >= 9:
        patterns.append(clean_phone[-9:])
    if len(clean_phone) >= 11:
        patterns.append(clean_phone[-11:])

    for p in patterns:
        query = select(Tutor).where(Tutor.phone.ilike(f"%{p}%"))
        res = await db.execute(query)
        tutor = res.scalars().first()
        if tutor:
            return tutor
    return None


async def process_meta_webhook(
    db: AsyncSession,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Processa o payload de eventos da Meta Cloud API (mensagens recebidas e status).
    Garante idempotência e armazena os registros na tabela whatsapp_messages.
    """
    messages_processed = 0
    statuses_processed = 0
    duplicates_skipped = 0
    details = []

    # Busca a organização padrão para tenant_id
    org_res = await db.execute(select(Organization.id).limit(1))
    default_tenant_id = org_res.scalar_one_or_none()
    if not default_tenant_id:
        logger.error("[WhatsApp] Nenhuma organização encontrada para associar as mensagens.")
        return {
            "status": "error",
            "error": "Nenhuma organização configurada"
        }

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            field = change.get("field")

            if field != "messages" and "messages" not in value and "statuses" not in value:
                continue

            # 1. Processar Mensagens Recebidas (INBOUND)
            incoming_messages = value.get("messages", [])
            contacts = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}

            for msg in incoming_messages:
                msg_id = msg.get("id")
                from_phone = msg.get("from")
                msg_type = msg.get("type", "text")

                if not msg_id or not from_phone:
                    continue

                # Garantia de Idempotência: Se já processamos este message_id, ignora duplicação
                existing = await get_message_by_meta_id(db, msg_id)
                if existing:
                    logger.info(f"[WhatsApp Idempotência] Mensagem {msg_id} já gravada anteriormente. Pulando.")
                    duplicates_skipped += 1
                    continue

                # Extração do conteúdo conforme tipo da mensagem
                content: Optional[str] = None
                if msg_type == "text":
                    content = msg.get("text", {}).get("body")
                elif msg_type == "button":
                    content = msg.get("button", {}).get("text")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    inter_type = interactive.get("type")
                    if inter_type == "button_reply":
                        content = interactive.get("button_reply", {}).get("title")
                    elif inter_type == "list_reply":
                        content = interactive.get("list_reply", {}).get("title")
                elif msg_type == "audio":
                    content = "[Áudio recebido]"
                elif msg_type == "image":
                    caption = msg.get("image", {}).get("caption")
                    content = f"[Imagem recebida]: {caption}" if caption else "[Imagem recebida]"
                else:
                    content = f"[{msg_type.upper()}]"

                # Associação automática com tutor
                tutor = await find_tutor_by_phone(db, from_phone)

                whatsapp_record = WhatsAppMessage(
                    tenant_id=tutor.tenant_id if tutor else default_tenant_id,
                    message_id=msg_id,
                    phone=from_phone,
                    direction="INBOUND",
                    message_type=msg_type,
                    content=content,
                    status="received",
                    tutor_id=tutor.id if tutor else None,
                    raw_payload=msg
                )
                db.add(whatsapp_record)
                messages_processed += 1
                details.append({
                    "action": "saved_message",
                    "message_id": msg_id,
                    "phone": from_phone,
                    "tutor_id": str(tutor.id) if tutor else None
                })

            # 2. Processar Atualizações de Status (sent, delivered, read, failed)
            status_updates = value.get("statuses", [])
            for st in status_updates:
                st_msg_id = st.get("id")
                new_status = st.get("status")
                if not st_msg_id or not new_status:
                    continue

                existing = await get_message_by_meta_id(db, st_msg_id)
                if existing:
                    existing.status = new_status
                    statuses_processed += 1
                    details.append({
                        "action": "updated_status",
                        "message_id": st_msg_id,
                        "new_status": new_status
                    })

    await db.commit()

    return {
        "status": "ok",
        "messages_processed": messages_processed,
        "statuses_processed": statuses_processed,
        "duplicate_messages_skipped": duplicates_skipped,
        "details": details
    }


async def list_whatsapp_messages(
    db: AsyncSession,
    phone: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[WhatsAppMessage]:
    """Lista o histórico de mensagens trocadas via WhatsApp para auditoria ou atendimento."""
    query = select(WhatsAppMessage)
    if phone:
        clean_phone = "".join(filter(str.isdigit, phone))
        query = query.where(WhatsAppMessage.phone.ilike(f"%{clean_phone}%"))
    query = query.order_by(WhatsAppMessage.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

