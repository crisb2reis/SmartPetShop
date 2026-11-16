import hmac
import hashlib
import logging
import uuid
from typing import Optional, List, Dict, Any, Tuple
import httpx
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


# ============================================================================
# Serviços de Envio de Mensagens (Outbound via Meta Cloud API)
# ============================================================================

def clean_phone_number(phone: str) -> str:
    """Normaliza o telefone para formato internacional E.164 (ex: 5511999998888)."""
    digits = "".join(filter(str.isdigit, phone))
    # Se tiver 10 ou 11 dígitos no Brasil (sem DDI 55), adiciona 55
    if len(digits) in (10, 11) and not digits.startswith("55"):
        digits = f"55{digits}"
    return digits


async def send_whatsapp_payload(
    db: AsyncSession,
    recipient_phone: str,
    payload_type: str,
    payload_data: Dict[str, Any],
    content_summary: str,
    tenant_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Despacha uma mensagem via WhatsApp Meta Cloud API (ou simulação em desenvolvimento).
    Garante gravação do registro OUTBOUND na tabela whatsapp_messages para auditoria.
    """
    clean_phone = clean_phone_number(recipient_phone)
    tutor = await find_tutor_by_phone(db, clean_phone)

    if not tenant_id:
        if tutor:
            tenant_id = tutor.tenant_id
        else:
            org_res = await db.execute(select(Organization.id).limit(1))
            tenant_id = org_res.scalar_one_or_none()

    mode = "simulation"
    meta_message_id: Optional[str] = None
    delivery_status = "sent"
    error_msg: Optional[str] = None

    # Se configurado token e phone_number_id reais da Meta, despacha via HTTP
    if settings.WHATSAPP_API_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
        mode = "meta_api"
        url = f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload_data, headers=headers)
                if resp.status_code in (200, 201):
                    res_json = resp.json()
                    meta_message_id = res_json.get("messages", [{}])[0].get("id")
                    delivery_status = "sent"
                    logger.info(f"[WhatsApp Meta API] Mensagem enviada com sucesso para {clean_phone}: {meta_message_id}")
                else:
                    error_msg = f"HTTP {resp.status_code}: {resp.text}"
                    delivery_status = "failed"
                    logger.error(f"[WhatsApp Meta API] Erro ao enviar mensagem para {clean_phone}: {error_msg}")
        except Exception as e:
            error_msg = f"Exceção ao conectar com a Meta API: {str(e)}"
            delivery_status = "failed"
            logger.error(f"[WhatsApp Meta API] Falha de conexão: {e}", exc_info=True)

    if not meta_message_id:
        # Gera ID simulado para ambiente local / testes
        meta_message_id = f"wamid.OUTBOUND_{uuid.uuid4().hex[:16]}"

    # Salva no banco de dados para auditoria completa
    msg_record = WhatsAppMessage(
        tenant_id=tenant_id,
        message_id=meta_message_id,
        phone=clean_phone,
        direction="OUTBOUND",
        message_type=payload_type,
        content=content_summary,
        status=delivery_status,
        tutor_id=tutor.id if tutor else None,
        raw_payload={
            "request_payload": payload_data,
            "mode": mode,
            "error": error_msg
        }
    )
    db.add(msg_record)
    await db.commit()
    await db.refresh(msg_record)

    return {
        "success": delivery_status != "failed",
        "message_id": meta_message_id,
        "status": delivery_status,
        "recipient": clean_phone,
        "mode": mode,
        "error": error_msg,
        "details": {
            "tutor_id": str(tutor.id) if tutor else None,
            "tutor_name": tutor.name if tutor else None,
            "payload_type": payload_type
        }
    }


async def send_text_message(
    db: AsyncSession,
    phone: str,
    text: str,
    tenant_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """Dispara uma mensagem de texto simples ou formatada via WhatsApp."""
    clean_phone = clean_phone_number(phone)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    return await send_whatsapp_payload(
        db=db,
        recipient_phone=clean_phone,
        payload_type="text",
        payload_data=payload,
        content_summary=text,
        tenant_id=tenant_id
    )


async def send_interactive_buttons(
    db: AsyncSession,
    phone: str,
    body_text: str,
    buttons: List[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = "SmartPetShop 🐾",
    tenant_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """Dispara uma mensagem interativa com até 3 botões de resposta rápida."""
    clean_phone = clean_phone_number(phone)
    btn_elements = [
        {
            "type": "reply",
            "reply": {
                "id": b["id"],
                "title": b["title"][:20]
            }
        }
        for b in buttons[:3]
    ]

    interactive_obj: Dict[str, Any] = {
        "type": "button",
        "body": {"text": body_text},
        "action": {"buttons": btn_elements}
    }
    if header_text:
        interactive_obj["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive_obj["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "interactive",
        "interactive": interactive_obj
    }

    buttons_label = " | ".join([b["title"] for b in buttons[:3]])
    content_summary = f"{body_text}\n[Botões: {buttons_label}]"

    return await send_whatsapp_payload(
        db=db,
        recipient_phone=clean_phone,
        payload_type="interactive",
        payload_data=payload,
        content_summary=content_summary,
        tenant_id=tenant_id
    )


async def send_template_message(
    db: AsyncSession,
    phone: str,
    template_name: str,
    language_code: str = "pt_BR",
    parameters: Optional[List[str]] = None,
    tenant_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """Dispara um template oficial HSM aprovado na Meta Cloud API."""
    clean_phone = clean_phone_number(phone)
    params = parameters or []
    param_components = [{"type": "text", "text": str(p)} for p in params]

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code}
        }
    }
    if param_components:
        payload["template"]["components"] = [
            {
                "type": "body",
                "parameters": param_components
            }
        ]

    content_summary = f"[Template HSM: {template_name}] Parâmetros: {params}"

    return await send_whatsapp_payload(
        db=db,
        recipient_phone=clean_phone,
        payload_type="template",
        payload_data=payload,
        content_summary=content_summary,
        tenant_id=tenant_id
    )


async def send_vaccine_reminder_message(
    db: AsyncSession,
    phone: str,
    pet_name: str,
    vaccine_name: str,
    due_date: str,
    alert_type: str = "vaccine_d7",
    tenant_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """Dispara um alerta oficial de reforço de vacina com botões de ação rápida para agendamento."""
    clean_phone = clean_phone_number(phone)
    tutor = await find_tutor_by_phone(db, clean_phone)
    tutor_name = tutor.name if tutor else "Tutor(a)"

    if alert_type == "vaccine_overdue":
        header = "⚠️ ALERTA DE VACINA ATRASADA"
        body = (
            f"Olá {tutor_name}! ⚠️ A vacina *{vaccine_name}* do seu pet *{pet_name}* está *vencida* (data limite: {due_date}).\n\n"
            f"A imunização contínua é fundamental para protegê-lo contra zoonoses graves e viroses. "
            f"Vamos garantir a proteção dele hoje mesmo?"
        )
    elif alert_type == "vaccine_d0":
        header = "🚨 VACINA VENCE HOJE"
        body = (
            f"Olá {tutor_name}! 🚨 Hoje ({due_date}) é a data prevista para a aplicação da vacina *{vaccine_name}* do *{pet_name}*.\n\n"
            f"Traga-o ao nosso pet shop para aplicação com o médico veterinário responsável!"
        )
    elif alert_type == "vaccine_d7":
        header = "🐾 LEMBRETE DE VACINA"
        body = (
            f"Olá {tutor_name}! 🐾 Passando para lembrar que a vacina *{vaccine_name}* do *{pet_name}* vence em breve ({due_date}).\n\n"
            f"Que tal já deixar o horário garantido na nossa agenda?"
        )
    else:  # vaccine_d30
        header = "📋 AVISO PRÉVIO DE REFORÇO"
        body = (
            f"Oi {tutor_name}! 📋 A dose de reforço da vacina *{vaccine_name}* do *{pet_name}* está prevista para o próximo mês ({due_date}).\n\n"
            f"Fique atento ao calendário para manter a caderneta digital sempre em dia!"
        )

    buttons = [
        {"id": "btn_agendar_vacina", "title": "Agendar Vacina 💉"},
        {"id": "btn_falar_atendente", "title": "Falar com Atendente 🙋‍♂️"}
    ]

    return await send_interactive_buttons(
        db=db,
        phone=clean_phone,
        body_text=body,
        buttons=buttons,
        header_text=header,
        footer_text="SmartPetShop 🐾 CFMV Digital",
        tenant_id=tenant_id
    )

