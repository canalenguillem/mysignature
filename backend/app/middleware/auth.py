"""Middleware de rate limiting para los endpoints de autenticación.

docs/API_SPEC.md §9: `/auth/validate-cert` 10 req/min por IP.
La validación del JWT por request se hace vía dependencia `get_current_user`
en cada ruta protegida (patrón idiomático de FastAPI), no en este middleware.

Usa un contador en Redis con TTL de 60s (docs/DATABASE.md §3, Rate Limiting).
Si Redis no está disponible, el límite se omite (fail-open) para no tumbar la API.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.database.connection import get_redis
from app.utils.logger import logger

_WINDOW_SECONDS = 60


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/auth"):
            limited = self._rate_limited(request)
            if limited is not None:
                return limited
        return await call_next(request)

    def _rate_limited(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{request.url.path}"
        try:
            redis_client = get_redis()
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, _WINDOW_SECONDS)
            if current > settings.AUTH_RATE_LIMIT_PER_MIN:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": _WINDOW_SECONDS,
                    },
                )
        except Exception as exc:  # noqa: BLE001 — fail-open ante fallo de Redis
            logger.warning("Rate limiter deshabilitado (Redis): %s", exc)
        return None
