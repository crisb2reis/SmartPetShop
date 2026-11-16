import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.core.database import AsyncSessionLocal
from app.agents.alert_agent import predictive_alert_agent
from app.services.whatsapp_queue import whatsapp_queue
from app.api.v1.router import api_router

logger = logging.getLogger("smartpetshop.scheduler")


async def periodic_vaccine_checker():
    """Tarefa em background que verifica periodicamente o vencimento de vacinas (CFMV)."""
    # Espera 10 segundos após a inicialização para executar a primeira checagem
    await asyncio.sleep(10)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                result = await predictive_alert_agent.scan_vaccine_reminders(db)
                logger.info(f"[Scheduler] Varredura de vacinas concluída: {result.get('alerts_generated', 0)} novos alertas.")
        except Exception as e:
            logger.warning(f"[Scheduler] Falha na varredura de vacinas: {e}")
        # Executa a cada 12 horas (43.200 segundos)
        await asyncio.sleep(43200)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o worker em background do scheduler de vacinas
    vaccine_task = asyncio.create_task(periodic_vaccine_checker())

    # Inicializa o worker assíncrono da fila de eventos do WhatsApp (Fila & IA)
    if settings.WHATSAPP_WORKER_ENABLED:
        await whatsapp_queue.start_worker()

    yield

    # Finaliza workers no encerramento da aplicação
    if settings.WHATSAPP_WORKER_ENABLED:
        await whatsapp_queue.stop_worker()

    vaccine_task.cancel()
    try:
        await vaccine_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 1. Middleware de Cabeçalhos de Segurança (OWASP Top 10)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Middleware de Rate Limiting (Anti-DDoS / Anti-BruteForce)
app.add_middleware(
    RateLimitMiddleware,
    general_limit=120,   # Máximo 120 requisições por minuto para endpoints gerais
    ai_limit=20,         # Máximo 20 requisições por minuto para chat / IA
    window_seconds=60
)

# 3. CORS Permissivo para Desenvolvimento Local
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

# 4. Registra endpoints da API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_host": settings.POSTGRES_HOST,
        "database_name": settings.POSTGRES_DB
    }
