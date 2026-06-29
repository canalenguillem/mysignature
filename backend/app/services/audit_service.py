"""Servicio de auditoría: registro inmutable de operaciones.

Escribe en `audit_logs` (tabla protegida contra UPDATE/DELETE por triggers,
ver init.sql). Diseñado para no romper el flujo de negocio si el log falla.

Referencia: docs/IMPLEMENTATION_ORDER.md Tarea 5.4 · docs/API_SPEC.md §5
(Se adelanta aquí porque la firma de la Fase 4 debe quedar auditada.)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from starlette.requests import Request

from sqlalchemy import desc

from app.models.audit_log import AuditEvent, AuditLog
from app.utils.logger import logger


class AuditService:
    @staticmethod
    async def log_action(
        db: Session,
        action: str,
        actor_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        actor_cert_fingerprint: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        ip_address = None
        user_agent = None
        if request is not None:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        entry = AuditLog(
            timestamp=datetime.utcnow(),
            action=action,
            actor_id=actor_id,
            actor_cert_fingerprint=actor_cert_fingerprint,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        try:
            db.add(entry)
            db.commit()
        except Exception as exc:  # noqa: BLE001 — auditoría nunca debe tumbar el flujo
            db.rollback()
            logger.error("No se pudo escribir audit_log (%s): %s", action, exc)

    # ----- lectura -----
    @staticmethod
    def list_for_document(
        db: Session,
        document_id: str,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        q = db.query(AuditLog).filter(
            AuditLog.resource_type == "document",
            AuditLog.resource_id == document_id,
        )
        if action:
            q = q.filter(AuditLog.action == action)
        total = q.count()
        items = q.order_by(desc(AuditLog.timestamp)).limit(limit).offset(offset).all()
        return {"total": total, "limit": limit, "offset": offset, "audit_logs": items}

    @staticmethod
    def list_events(
        db: Session,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> dict:
        q = db.query(AuditEvent)
        if event_type:
            q = q.filter(AuditEvent.event_type == event_type)
        if severity:
            q = q.filter(AuditEvent.severity == severity)
        if date_from:
            q = q.filter(AuditEvent.timestamp >= date_from)
        if date_to:
            q = q.filter(AuditEvent.timestamp <= date_to)
        total = q.count()
        items = q.order_by(desc(AuditEvent.timestamp)).limit(limit).all()
        return {"total": total, "events": items}
