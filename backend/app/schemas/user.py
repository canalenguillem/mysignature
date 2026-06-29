"""Schemas Pydantic para búsqueda de usuarios (asignación de firmas).

Referencia: docs/API_SPEC.md §7
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserSearchResult(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    organization: Optional[str] = None
    cert_fingerprint: str
    cert_expires: Optional[datetime] = None
    cert_valid: bool
    last_login: Optional[datetime] = None


class UserSearchResponse(BaseModel):
    total: int
    results: List[UserSearchResult]


class OrgUser(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    cert_valid: bool
    cert_expires: Optional[datetime] = None


class OrgUsersResponse(BaseModel):
    organization: str
    total: int
    users: List[OrgUser]
