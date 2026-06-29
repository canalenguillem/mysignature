"""Middleware de cabeceras de seguridad.

Complementa las cabeceras de nginx (docs/DOCKER.md §4) para los accesos
directos al backend. Referencia: docs/BACKEND_SPEC.md (middleware/security.py)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in _HEADERS.items():
            response.headers.setdefault(key, value)
        return response
