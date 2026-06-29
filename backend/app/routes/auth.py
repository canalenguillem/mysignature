"""Rutas de autenticación.

Endpoints (docs/API_SPEC.md §1 y §6):
  POST /auth/validate-cert  -> valida certificado y emite JWT
  POST /auth/refresh        -> renueva access token
  POST /auth/logout         -> revoca refresh token
  GET  /auth/me             -> usuario autenticado
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    CertificateValidationRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    UserPublic,
)
from app.schemas.workflow import (
    PendingCreatedBy,
    PendingSignatureItem,
    PendingSignaturesResponse,
    PendingWorkflowInfo,
)
from app.services.workflow_service import WorkflowService
from app.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    revoke_refresh_token,
    verify_refresh_token,
)
from app.services.certificate_service import CertificateService
from app.utils.logger import logger

router = APIRouter()


@router.post("/validate-cert", response_model=AuthResponse)
async def validate_certificate(
    request: CertificateValidationRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Valida el certificado del cliente y devuelve tokens + usuario."""
    cert_data = CertificateService.validate_certificate_chain(request.certificate_pem)
    user = CertificateService.get_or_create_user(db, cert_data)

    access_token = create_access_token(
        subject=str(user.id), expires_in=settings.JWT_EXPIRATION_MINUTES
    )
    refresh_token = create_refresh_token(user.id, db)

    logger.info("Usuario autenticado id=%s fp=%s", user.id, user.cert_fingerprint)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(request: RefreshRequest) -> RefreshResponse:
    """Renueva el access token a partir de un refresh token válido."""
    user_id = verify_refresh_token(request.refresh_token)
    access_token = create_access_token(
        subject=str(user_id), expires_in=settings.JWT_EXPIRATION_MINUTES
    )
    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: User = Depends(get_current_user)) -> LogoutResponse:
    """Invalida el refresh token del usuario actual."""
    revoke_refresh_token(current_user.id)
    logger.info("Logout usuario id=%s", current_user.id)
    return LogoutResponse()


@router.get("/me", response_model=MeResponse)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Devuelve la información del usuario autenticado."""
    return MeResponse.model_validate(current_user)


@router.get("/my-pending-signatures", response_model=PendingSignaturesResponse)
async def my_pending_signatures(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PendingSignaturesResponse:
    """Documentos con una firma pendiente del usuario actual."""
    pending = WorkflowService.get_pending_for_user(db, current_user)
    items = []
    for p in pending:
        wf, doc = p["workflow"], p["document"]
        creator = wf.document.owner if wf.document else None
        items.append(
            PendingSignatureItem(
                document_id=doc.id,
                title=doc.title,
                created_by=PendingCreatedBy(
                    first_name=creator.first_name if creator else None,
                    last_name=creator.last_name if creator else None,
                ),
                created_at=doc.created_at,
                workflow=PendingWorkflowInfo(
                    workflow_id=wf.id,
                    type=wf.sequence_type,
                    completed_signers=wf.completed_signers,
                    required_signers=wf.required_signers,
                ),
            )
        )
    return PendingSignaturesResponse(total=len(items), pending_signatures=items)
