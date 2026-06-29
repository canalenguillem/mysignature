"""Entrada ASGI de la API de Firma Digital eIDAS.

Referencia: docs/BACKEND_SPEC.md §app/main.py

Nota: los routers de documentos/firmas/workflows se montan en sus fases
correspondientes (Fase 3-5 del IMPLEMENTATION_ORDER). Aquí va el de auth (Fase 2).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.middleware import AuthMiddleware, SecurityHeadersMiddleware
from app.routes import audit, auth, documents, signatures, users, workflows
from app.utils.errors import ApiError
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación %s...", settings.APP_NAME)
    await init_db()
    yield
    logger.info("Deteniendo aplicación...")


app = FastAPI(
    title="Firma Digital EIDAS",
    description="Plataforma de firma digital con certificados FNMT",
    version="1.0.0",
    lifespan=lifespan,
)

# ===== Middlewares =====
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-SSL-Client-Cert"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthMiddleware)


# ===== Manejo de errores (docs/API_SPEC.md §8) =====
@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


# ===== Rutas =====
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(signatures.router, prefix="/api/v1/documents", tags=["signatures"])
app.include_router(workflows.router, prefix="/api/v1/documents", tags=["workflows"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
