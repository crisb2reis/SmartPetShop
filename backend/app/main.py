from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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
