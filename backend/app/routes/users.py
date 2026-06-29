"""Rutas de búsqueda de usuarios (asignación de firmas).

  GET /users/search?query=&org=&limit=
  GET /users/by-organization/{organization}

Referencia: docs/API_SPEC.md §7
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import (
    OrgUser,
    OrgUsersResponse,
    UserSearchResponse,
    UserSearchResult,
)
from app.security.jwt_handler import get_current_user
from app.services.user_service import UserService

router = APIRouter()


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: Optional[str] = Query(None),
    org: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSearchResponse:
    users = UserService.search(db, query=query, org=org, limit=limit)
    return UserSearchResponse(
        total=len(users),
        results=[
            UserSearchResult(
                id=u.id,
                name=UserService.full_name(u),
                email=u.email,
                organization=u.organization,
                cert_fingerprint=u.cert_fingerprint,
                cert_expires=u.cert_not_after,
                cert_valid=UserService.cert_valid(u),
                last_login=u.last_login,
            )
            for u in users
        ],
    )


@router.get("/by-organization/{organization}", response_model=OrgUsersResponse)
async def users_by_organization(
    organization: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgUsersResponse:
    users = UserService.by_organization(db, organization)
    return OrgUsersResponse(
        organization=organization,
        total=len(users),
        users=[
            OrgUser(
                id=u.id,
                name=UserService.full_name(u),
                email=u.email,
                cert_valid=UserService.cert_valid(u),
                cert_expires=u.cert_not_after,
            )
            for u in users
        ],
    )
