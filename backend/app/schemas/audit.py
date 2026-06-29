"""Schemas Pydantic para auditoría.

Referencia: docs/API_SPEC.md §5
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AuditActor(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    cert_fingerprint: Optional[str] = None


class AuditLogItem(BaseModel):
    id: int
    timestamp: datetime
    action: str
    actor: Optional[AuditActor] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    success: bool = True


class AuditLogResponse(BaseModel):
    total: int
    limit: int
    offset: int
    audit_logs: List[AuditLogItem]


class AuditEventItem(BaseModel):
    id: int
    timestamp: datetime
    event_type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[dict] = None


class AuditEventsResponse(BaseModel):
    total: int
    events: List[AuditEventItem]
