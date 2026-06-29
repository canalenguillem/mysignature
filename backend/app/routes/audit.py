"""Rutas de auditoría (montadas bajo /api/v1).

  GET /documents/{id}/audit   -> log de auditoría de un documento
  GET /audit/events           -> búsqueda global de eventos (admin)

Referencia: docs/API_SPEC.md §5
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.audit import (
    AuditActor,
    AuditEventItem,
    AuditEventsResponse,
    AuditLogItem,
    AuditLogResponse,
)
from app.security.jwt_handler import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/documents/{document_id}/audit", response_model=AuditLogResponse)
async def document_audit(
    document_id: str,
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditLogResponse:
    result = AuditService.list_for_document(
        db, document_id, action=action, limit=limit, offset=offset
    )
    return AuditLogResponse(
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        audit_logs=[
            AuditLogItem(
                id=log.id,
                timestamp=log.timestamp,
                action=log.action,
                actor=AuditActor(
                    first_name=log.actor.first_name if log.actor else None,
                    last_name=log.actor.last_name if log.actor else None,
                    cert_fingerprint=log.actor_cert_fingerprint,
                ),
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                success=log.success,
            )
            for log in result["audit_logs"]
        ],
    )


@router.get("/audit/events", response_model=AuditEventsResponse)
async def audit_events(
    action: Optional[str] = Query(None, alias="action"),
    severity: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditEventsResponse:
    result = AuditService.list_events(
        db, event_type=action, severity=severity,
        date_from=date_from, date_to=date_to, limit=limit,
    )
    return AuditEventsResponse(
        total=result["total"],
        events=[
            AuditEventItem(
                id=e.id,
                timestamp=e.timestamp,
                event_type=e.event_type,
                severity=e.severity,
                message=e.message,
                metadata=e.event_metadata,
            )
            for e in result["events"]
        ],
    )
