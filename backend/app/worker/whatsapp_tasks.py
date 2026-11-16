import asyncio
import logging
from typing import Any, Dict
from app.worker.celery_app import celery_app
from app.core.config import settings
from app.services.whatsapp_queue import whatsapp_queue, WhatsAppJob

logger = logging.getLogger("smartpetshop.celery.whatsapp")


@celery_app.task(
    bind=True,
    name="whatsapp.process_incoming_payload",
    max_retries=settings.WHATSAPP_QUEUE_MAX_RETRIES,
    default_retry_delay=int(settings.WHATSAPP_QUEUE_RETRY_BACKOFF)
)
def process_incoming_payload_task(self, payload: Dict[str, Any], job_id: str = None):
    """
    Tarefa Celery para processar payloads recebidos da Meta Cloud API.
    Aplica retentativa automática com backoff exponencial caso ocorram falhas de rede/API.
    """
    logger.info(f"[Celery WhatsApp Task] Iniciando processamento do payload (Job: {job_id}, Tentativa: {self.request.retries + 1})...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        job = WhatsAppJob(payload=payload, job_id=job_id)
        job.attempts = self.request.retries + 1
        result = loop.run_until_complete(whatsapp_queue._execute_job(job))
        logger.info(f"[Celery WhatsApp Task] Payload processado com sucesso!")
        return result
    except Exception as exc:
        logger.warning(f"[Celery WhatsApp Task] Erro na tentativa {self.request.retries + 1}: {exc}")
        # Backoff exponencial para Celery: delay = base * (2 ** retries)
        countdown = int(settings.WHATSAPP_QUEUE_RETRY_BACKOFF ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
    finally:
        loop.close()
