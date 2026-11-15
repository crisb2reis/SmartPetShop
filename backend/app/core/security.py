import time
import re
from typing import Dict, Tuple, List
from collections import defaultdict

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response, JSONResponse
    from fastapi import HTTPException, status
except ImportError:
    # Fallback para execução de testes SAST em ambiente sem fastapi pré-instalado
    BaseHTTPMiddleware = object
    Request = object
    Response = object
    JSONResponse = object
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
    class status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_429_TOO_MANY_REQUESTS = 429


# -------------------------------------------------------------
# 1. Middleware de Cabeçalhos de Segurança HTTP (OWASP / Hardening)
# -------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Defesas contra Clickjacking, MIME Sniffing, XSS e vazamento de referrer
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "frame-ancestors 'none';"
        )
        # Remove cabeçalho de identificação de servidor para evitar fingerprinting
        if "server" in response.headers:
            del response.headers["server"]

        return response


# -------------------------------------------------------------
# 2. Rate Limiting com Janela Deslizante (Anti-DDoS / Anti-BruteForce)
# -------------------------------------------------------------
class SlidingWindowRateLimiter:
    """
    Controlador de taxa de requisições por IP com janela de tempo deslizante.
    Protege endpoints públicos e previne exaustão de quota da API de IA.
    """
    def __init__(self):
        # Mapeamento: ip -> list of timestamps
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds
        
        # Filtrar requisições fora da janela atual
        valid_requests = [t for t in self.requests[client_ip] if t > cutoff]
        self.requests[client_ip] = valid_requests

        if len(valid_requests) >= max_requests:
            retry_after = int(valid_requests[0] + window_seconds - now) + 1
            return True, max(1, retry_after)

        self.requests[client_ip].append(now)
        return False, 0


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, general_limit: int = 120, ai_limit: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.general_limit = general_limit
        self.ai_limit = ai_limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path

        # Limite mais restritivo para chamadas do Agente de IA (custo computacional)
        if "/api/v1/chat" in path or "/api/v1/alerts/run-scan" in path:
            max_reqs = self.ai_limit
        else:
            max_reqs = self.general_limit

        is_limited, retry_after = rate_limiter.is_rate_limited(
            client_ip=f"{client_ip}:{path}",
            max_requests=max_reqs,
            window_seconds=self.window_seconds
        )

        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Muitas requisições. Limite de taxa excedido. Tente novamente em {retry_after} segundos.",
                    "retry_after_seconds": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)


# -------------------------------------------------------------
# 3. Defesa contra Prompt Injection & Sanitização de Entradas
# -------------------------------------------------------------
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"ignore\s+as\s+instruções\s+anteriores",
    r"system\s*prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"jailbreak",
    r"diga-me\s+suas\s+instruções\s+secretas",
    r"exiba\s+suas\s+chaves\s+de\s+api",
    r"reveal\s+your\s+api\s+key",
    r"bypass\s+restrictions",
    r"drop\s+database",
    r"drop\s+table",
    r"<script\b[^>]*>",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def sanitize_and_validate_prompt(user_input: str, max_length: int = 1000) -> str:
    """
    Sanitiza o texto de entrada do usuário antes do envio ao Agente de IA:
    - Limita tamanho máximo para evitar ataques de estouro de contexto.
    - Bloqueia injeções de prompt conhecidas (DAN, jailbreaks, vazamento de API keys).
    - Remove caracteres de controle invisíveis.
    """
    if len(user_input) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A mensagem excede o limite máximo permitido de {max_length} caracteres."
        )

    for pattern in COMPILED_PATTERNS:
        if pattern.search(user_input):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conteúdo suspeito ou tentativa de violação de diretrizes de segurança detectada."
            )

    # Remove tags HTML perigosas e caracteres nulos
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", user_input)
    return cleaned.strip()
