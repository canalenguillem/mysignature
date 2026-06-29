"""Búsqueda de usuarios para asignación de firmas (OPCIÓN 3 HÍBRIDA).

- Búsqueda por email o nombre (case-insensitive).
- Solo usuarios que ya se autenticaron (todos los registros de `users` lo son).
- Marca `cert_valid` según la vigencia del certificado.

Referencia: docs/ARCHITECTURE.md §Selección de usuarios · docs/API_SPEC.md §7
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.user import User


def _full_name(u: User) -> str:
    return " ".join(p for p in [u.first_name, u.last_name] if p).strip() or (u.email or "")


def _cert_valid(u: User) -> bool:
    return bool(u.cert_not_after and u.cert_not_after > datetime.utcnow())


class UserService:
    @staticmethod
    def search(
        db: Session,
        query: Optional[str] = None,
        org: Optional[str] = None,
        limit: int = 20,
    ) -> list[User]:
        q = db.query(User).filter(User.is_active.is_(True))

        if query:
            like = f"%{query.lower()}%"
            q = q.filter(
                or_(
                    func.lower(User.email).like(like),
                    func.lower(User.first_name).like(like),
                    func.lower(User.last_name).like(like),
                    func.lower(func.concat(User.first_name, " ", User.last_name)).like(like),
                )
            )
        if org:
            q = q.filter(func.lower(User.organization) == org.lower())

        return q.order_by(User.first_name, User.last_name).limit(limit).all()

    @staticmethod
    def by_organization(db: Session, organization: str) -> list[User]:
        return (
            db.query(User)
            .filter(
                User.is_active.is_(True),
                func.lower(User.organization) == organization.lower(),
            )
            .order_by(User.first_name, User.last_name)
            .all()
        )

    # helpers expuestos para los serializadores de las rutas
    full_name = staticmethod(_full_name)
    cert_valid = staticmethod(_cert_valid)
