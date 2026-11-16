import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services import whatsapp_service
from app.agents.chatbot_agent import chatbot_agent

logger = logging.getLogger("smartpetshop.whatsapp.queue")


class WhatsAppJob:
    """Representa um payload enfileirado para processamento assíncrono."""

    def __init__(self, payload: Dict[str, Any], job_id: Optional[str] = None):
        self.job_id: str = job_id or str(uuid.uuid4())
        self.payload: Dict[str, Any] = payload
        self.status: str = "queued"  # queued, processing, completed, failed, retry_pending
        self.attempts: int = 0
        self.max_retries: int = settings.WHATSAPP_QUEUE_MAX_RETRIES
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = self.created_at
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "result": self.result
        }


class WhatsAppQueueManager:
    """
    Gerenciador de fila e worker assíncrono para eventos da Meta Cloud API.
    Possui suporte integrado para:
    - Broker Redis quando disponível (com persistência em Redis List).
    - Fallback gracioso automático para fila in-memory (asyncio.Queue).
    - Retentativas automáticas com Backoff Exponencial.
    - Mecanismo de contingência e fallback humanizado caso os serviços de IA falhem.
    """

    def __init__(self):
        self._memory_queue: asyncio.Queue[WhatsAppJob] = asyncio.Queue()
        self._jobs_store: Dict[str, WhatsAppJob] = {}
        self._max_stored_jobs: int = 1000
        self._is_running: bool = False
        self._worker_task: Optional[asyncio.Task] = None
        self._redis_client = None
        self._redis_available: bool = False
        self._total_processed: int = 0
        self._total_failed: int = 0
        self._total_retried: int = 0

    async def initialize(self):
        """Inicializa conexões e testa disponibilidade do Redis."""
        try:
            import redis.asyncio as aioredis
            redis_url = settings.redis_connection_url
            client = aioredis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            await client.ping()
            self._redis_client = client
            self._redis_available = True
            logger.info(f"[WhatsApp Queue] Conectado com sucesso ao Redis em {settings.REDIS_HOST}:{settings.REDIS_PORT}.")
        except Exception as e:
            self._redis_available = False
            self._redis_client = None
            logger.info(f"[WhatsApp Queue] Redis indisponível ou não configurado ({e}). Operando com fila assíncrona in-memory de alta performance.")

    async def start_worker(self):
        """Inicia o loop do worker em background."""
        if self._is_running:
            return

        await self.initialize()
        self._is_running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("[WhatsApp Worker] Worker assíncrono de WhatsApp iniciado com sucesso.")

    async def stop_worker(self):
        """Encerra o worker de forma graciosa."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        if self._redis_client:
            try:
                await self._redis_client.close()
            except Exception:
                pass
        logger.info("[WhatsApp Worker] Worker de WhatsApp finalizado.")

    async def enqueue(self, payload: Dict[str, Any]) -> WhatsAppJob:
        """Enfileira um payload bruto recebido da Meta Cloud API."""
        job = WhatsAppJob(payload=payload)
        self._jobs_store[job.job_id] = job

        # Limpeza periódica do histórico de jobs na memória
        if len(self._jobs_store) > self._max_stored_jobs:
            oldest_keys = list(self._jobs_store.keys())[:200]
            for k in oldest_keys:
                self._jobs_store.pop(k, None)

        if self._redis_available and self._redis_client:
            try:
                job_data = json.dumps({"job_id": job.job_id, "payload": payload})
                await self._redis_client.lpush("whatsapp:events:queue", job_data)
                logger.info(f"[WhatsApp Queue] Job {job.job_id} enfileirado no Redis.")
                return job
            except Exception as e:
                logger.warning(f"[WhatsApp Queue] Falha ao enfileirar no Redis ({e}). Fazendo fallback para fila in-memory.")
                self._redis_available = False

        # Fallback para fila in-memory
        await self._memory_queue.put(job)
        logger.info(f"[WhatsApp Queue] Job {job.job_id} enfileirado na memória.")
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Recupera informações de um job por seu ID."""
        job = self._jobs_store.get(job_id)
        return job.to_dict() if job else None

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas operacionais da fila e do worker."""
        queue_size = self._memory_queue.qsize()
        return {
            "is_running": self._is_running,
            "broker": "redis" if self._redis_available else "in-memory-asyncio",
            "redis_connected": self._redis_available,
            "in_memory_queue_size": queue_size,
            "total_processed": self._total_processed,
            "total_failed": self._total_failed,
            "total_retried": self._total_retried,
            "stored_jobs_count": len(self._jobs_store)
        }

    async def _worker_loop(self):
        """Loop contínuo de consumo de tarefas da fila."""
        while self._is_running:
            job: Optional[WhatsAppJob] = None
            try:
                # 1. Tenta consumir do Redis se disponível
                if self._redis_available and self._redis_client:
                    try:
                        raw = await self._redis_client.brpop("whatsapp:events:queue", timeout=1)
                        if raw:
                            _, raw_data = raw
                            parsed = json.loads(raw_data)
                            job_id = parsed.get("job_id")
                            job = self._jobs_store.get(job_id)
                            if not job:
                                job = WhatsAppJob(payload=parsed.get("payload", {}), job_id=job_id)
                                self._jobs_store[job.job_id] = job
                    except Exception as e:
                        logger.warning(f"[WhatsApp Worker] Erro no consumo do Redis ({e}). Alternando para in-memory.")
                        self._redis_available = False

                # 2. Se não consumiu do Redis, consome da fila in-memory
                if not job:
                    try:
                        job = await asyncio.wait_for(self._memory_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue

                if not job:
                    continue

                # 3. Processa a tarefa com retentativas automáticas
                await self._process_job_with_retries(job)

                if not self._redis_available:
                    self._memory_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WhatsApp Worker] Exceção inesperada no loop do worker: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_job_with_retries(self, job: WhatsAppJob):
        """Executa o processamento do job com suporte a retentativas e backoff exponencial."""
        job.status = "processing"
        job.updated_at = datetime.now(timezone.utc).isoformat()

        while job.attempts < job.max_retries:
            job.attempts += 1
            try:
                logger.info(f"[WhatsApp Worker] Processando job {job.job_id} (tentativa {job.attempts}/{job.max_retries})...")
                result = await self._execute_job(job)
                job.status = "completed"
                job.result = result
                job.updated_at = datetime.now(timezone.utc).isoformat()
                self._total_processed += 1
                logger.info(f"[WhatsApp Worker] Job {job.job_id} concluído com sucesso!")
                return

            except Exception as e:
                self._total_retried += 1
                error_msg = str(e)
                logger.warning(
                    f"[WhatsApp Worker] Falha no job {job.job_id} na tentativa {job.attempts}/{job.max_retries}: {error_msg}"
                )
                job.error = error_msg
                job.updated_at = datetime.now(timezone.utc).isoformat()

                if job.attempts < job.max_retries:
                    job.status = "retry_pending"
                    backoff_seconds = settings.WHATSAPP_QUEUE_RETRY_BACKOFF ** (job.attempts - 1)
                    logger.info(f"[WhatsApp Worker] Aguardando backoff de {backoff_seconds:.1f}s antes da próxima tentativa...")
                    await asyncio.sleep(backoff_seconds)
                else:
                    # Esgotou as tentativas
                    job.status = "failed"
                    self._total_failed += 1
                    logger.error(f"[WhatsApp Worker] Job {job.job_id} FALHOU definitivamente após {job.max_retries} tentativas.")
                    await self._handle_job_failure_contingency(job)
                    return

    async def _execute_job(self, job: WhatsAppJob) -> Dict[str, Any]:
        """
        Executa o pipeline completo:
        1. Persiste payload e atualiza status no banco com garantia de idempotência.
        2. Para cada mensagem do usuário, chama o Agente de IA (Rex).
        3. Se a IA responder, despacha a mensagem de volta pelo WhatsApp.
        """
        async with AsyncSessionLocal() as db:
            # 1. Processamento e Idempotência no banco de dados
            webhook_result = await whatsapp_service.process_meta_webhook(db, job.payload)

            ai_responses = []

            # 2. Varre as mensagens recebidas no payload para acionar o Agente de IA
            entries = job.payload.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    incoming_messages = value.get("messages", [])

                    for msg in incoming_messages:
                        from_phone = msg.get("from")
                        msg_type = msg.get("type", "text")
                        msg_id = msg.get("id")

                        # Extrai o texto conforme o tipo
                        user_text: Optional[str] = None
                        if msg_type == "text":
                            user_text = msg.get("text", {}).get("body")
                        elif msg_type == "button":
                            user_text = msg.get("button", {}).get("text")
                        elif msg_type == "interactive":
                            interactive = msg.get("interactive", {})
                            inter_type = interactive.get("type")
                            if inter_type == "button_reply":
                                user_text = interactive.get("button_reply", {}).get("title")
                            elif inter_type == "list_reply":
                                user_text = interactive.get("list_reply", {}).get("title")

                        if not from_phone or not user_text:
                            continue

                        # 3. Invoca o Agente Rex 🐾 com histórico e Tool Calling
                        agent_result = await chatbot_agent.process_whatsapp_message(
                            db=db,
                            from_phone=from_phone,
                            user_text=user_text
                        )

                        reply_text = agent_result.get("reply")
                        handoff_requested = agent_result.get("handoff_requested", False)
                        session_status = agent_result.get("status", "active")

                        # 4. Se houver resposta da IA e o atendimento não estiver em espera para humano
                        if reply_text:
                            # Dispara a resposta para o WhatsApp via Meta Cloud API / simulador
                            outbound_res = await whatsapp_service.send_text_message(
                                db=db,
                                phone=from_phone,
                                text=reply_text
                            )
                            ai_responses.append({
                                "message_id": msg_id,
                                "phone": from_phone,
                                "reply_sent": True,
                                "outbound_message_id": outbound_res.get("message_id"),
                                "handoff_requested": handoff_requested,
                                "session_status": session_status
                            })
                        else:
                            ai_responses.append({
                                "message_id": msg_id,
                                "phone": from_phone,
                                "reply_sent": False,
                                "handoff_requested": handoff_requested,
                                "session_status": session_status
                            })

            return {
                "webhook_result": webhook_result,
                "ai_responses": ai_responses
            }

    async def _handle_job_failure_contingency(self, job: WhatsAppJob):
        """Mecanismo de contingência disparado quando todas as retentativas falham."""
        try:
            # Tenta descobrir o remetente para enviar aviso de contingência
            entries = job.payload.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    messages = change.get("value", {}).get("messages", [])
                    for msg in messages:
                        phone = msg.get("from")
                        if phone:
                            async with AsyncSessionLocal() as db:
                                fallback_text = (
                                    "Olá! 🐾 Tivemos uma breve instabilidade técnica temporária no nosso sistema. "
                                    "Nossa equipe de recepção e atendimento já foi alertada e vai te responder "
                                    "pessoalmente por aqui em instantes. Obrigado pela compreensão!"
                                )
                                # Envia aviso ao cliente
                                await whatsapp_service.send_text_message(db, phone, fallback_text)

                                # Coloca sessão em human_required para aparecer no transbordo
                                session = await chatbot_agent.get_or_create_whatsapp_session(db, phone)
                                session.status = "human_required"
                                await db.commit()
                                logger.info(f"[WhatsApp Contingency] Mensagem de fallback enviada para {phone} e sessão marcada como human_required.")
        except Exception as fallback_err:
            logger.error(f"[WhatsApp Contingency] Falha ao executar procedimento de contingência: {fallback_err}")


# Instância Singleton do Gerenciador de Fila
whatsapp_queue = WhatsAppQueueManager()
