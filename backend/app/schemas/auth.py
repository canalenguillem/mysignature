"""Schemas Pydantic para autenticación.

Referencia: docs/API_SPEC.md §1 y §6
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ===== Requests =====
class CertificateValidationRequest(BaseModel):
    certificate_pem: str
    certificate_fingerprint: Optional[str] = None
    subject: Optional[dict] = None
    issuer: Optional[dict] = None
    serial_number: Optional[str] = None
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ===== Responses =====
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cert_fingerprint: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserPublic


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cert_fingerprint: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    cert_subject: Optional[dict] = None
    cert_issuer: Optional[dict] = None
    cert_not_after: Optional[datetime] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
