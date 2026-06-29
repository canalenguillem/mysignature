"""Servicio de certificados: validación + alta/actualización de usuario.

Orquesta `CertificateValidator` (security) con la persistencia del usuario.
Referencia: docs/BACKEND_SPEC.md §app/routes/auth.py (lógica de upsert de usuario)
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.security.certificates import CertificateValidator


def _split_name(common_name: str) -> tuple[str, str]:
    """Divide un CN 'Nombre Apellidos' en (first_name, last_name) de forma simple."""
    parts = (common_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


class CertificateService:
    """Fachada de validación de certificados usada por las rutas de auth."""

    @staticmethod
    def validate_certificate_chain(cert_pem: str) -> dict:
        return CertificateValidator.validate_certificate_chain(cert_pem)

    @staticmethod
    def get_or_create_user(db: Session, cert_data: dict) -> User:
        """Devuelve el usuario asociado al fingerprint, creándolo si no existe."""
        user = (
            db.query(User)
            .filter(User.cert_fingerprint == cert_data["fingerprint"])
            .first()
        )

        subject = cert_data.get("subject") or {}
        common_name = subject.get("commonName") or subject.get("CN") or ""
        first_name, last_name = _split_name(common_name)
        organization = subject.get("organizationName") or subject.get("O")
        email = cert_data.get("email") or subject.get("emailAddress")

        if user is None:
            user = User(
                cert_fingerprint=cert_data["fingerprint"],
                cert_subject=subject,
                cert_issuer=cert_data.get("issuer") or {},
                cert_serial=cert_data.get("serial_number"),
                cert_not_before=cert_data["not_before"],
                cert_not_after=cert_data["not_after"],
                first_name=first_name,
                last_name=last_name,
                organization=organization,
                email=email,
            )
            db.add(user)
        else:
            # Refrescar datos del certificado (puede haberse renovado).
            user.cert_subject = subject
            user.cert_issuer = cert_data.get("issuer") or {}
            user.cert_serial = cert_data.get("serial_number")
            user.cert_not_before = cert_data["not_before"]
            user.cert_not_after = cert_data["not_after"]
            if organization:
                user.organization = organization
            if email:
                user.email = email

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
