"""Validación de certificados X.509 (eIDAS / FNMT).

Referencia: docs/BACKEND_SPEC.md §app/security/certificates.py
           docs/API_SPEC.md §1 (códigos de error)
"""
from __future__ import annotations

from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtensionOID, NameOID

from app.utils.errors import (
    CertificateExpiredError,
    CertificateRevokedError,
    InvalidCertificateError,
    UntrustedIssuerError,
)
from app.utils.logger import logger

_TRUSTED_ISSUER_TOKENS = ("Fábrica Nacional", "FNMT")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Normaliza a UTC-aware (cryptography puede devolver naive)."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class CertificateValidator:
    """Valida certificados X.509 emitidos por la FNMT para firma eIDAS."""

    @staticmethod
    def validate_certificate_chain(cert_pem: str) -> dict:
        """Valida formato, vigencia, emisor, key usage y revocación.

        Devuelve un dict con los datos extraídos; lanza una `ApiError`
        (con error_code) si algo falla.
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
        except Exception as exc:  # noqa: BLE001
            raise InvalidCertificateError(f"Invalid certificate format: {exc}") from exc

        not_before = CertificateValidator._not_before(cert)
        not_after = CertificateValidator._not_after(cert)
        now = _now_utc()

        # 1. Vigencia
        if now < not_before:
            raise InvalidCertificateError("Certificate is not yet valid")
        if now > not_after:
            raise CertificateExpiredError("Certificate has expired")

        # 2. Emisor reconocido (FNMT)
        issuer_org = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if not any(
            tok in str(attr.value)
            for attr in issuer_org
            for tok in _TRUSTED_ISSUER_TOKENS
        ):
            raise UntrustedIssuerError("Untrusted certificate issuer")

        # 3. Key usage: debe permitir firma digital
        try:
            key_usage = cert.extensions.get_extension_for_oid(
                ExtensionOID.KEY_USAGE
            ).value
            if not key_usage.digital_signature:
                raise InvalidCertificateError(
                    "Certificate not authorized for digital signature"
                )
        except x509.ExtensionNotFound as exc:
            raise InvalidCertificateError(
                "Certificate missing key usage extension"
            ) from exc

        # 4. Revocación (OCSP/CRL) — placeholder, ver security/revocation.py
        if CertificateValidator._check_revocation(cert):
            raise CertificateRevokedError("Certificate has been revoked")

        return {
            "valid": True,
            "subject": CertificateValidator._extract_subject(cert),
            "issuer": CertificateValidator._extract_issuer(cert),
            "serial_number": str(cert.serial_number),
            "not_before": not_before.replace(tzinfo=None),
            "not_after": not_after.replace(tzinfo=None),
            "fingerprint": CertificateValidator._calculate_fingerprint(cert),
            "email": CertificateValidator._extract_email(cert),
        }

    # ----- helpers -----
    @staticmethod
    def _not_before(cert: x509.Certificate) -> datetime:
        dt = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before
        return _aware(dt)

    @staticmethod
    def _not_after(cert: x509.Certificate) -> datetime:
        dt = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after
        return _aware(dt)

    @staticmethod
    def _calculate_fingerprint(cert: x509.Certificate) -> str:
        """SHA-256 fingerprint en hex mayúsculas (64 chars)."""
        return cert.fingerprint(hashes.SHA256()).hex().upper()

    @staticmethod
    def _extract_subject(cert: x509.Certificate) -> dict:
        return {attr.oid._name: str(attr.value) for attr in cert.subject}

    @staticmethod
    def _extract_issuer(cert: x509.Certificate) -> dict:
        return {attr.oid._name: str(attr.value) for attr in cert.issuer}

    @staticmethod
    def _extract_email(cert: x509.Certificate) -> str | None:
        emails = cert.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)
        if emails:
            return str(emails[0].value)
        # Fallback: SubjectAlternativeName rfc822
        try:
            san = cert.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            ).value
            rfc822 = san.get_values_for_type(x509.RFC822Name)
            if rfc822:
                return str(rfc822[0])
        except x509.ExtensionNotFound:
            pass
        return None

    @staticmethod
    def _check_revocation(cert: x509.Certificate) -> bool:
        """Validar revocación (OCSP/CRL). TODO: implementar en Fase posterior."""
        logger.debug("Revocation check skipped (not implemented)")
        return False
