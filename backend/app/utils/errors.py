"""Excepciones de aplicación con código de error estable.

El handler registrado en `app.main` las serializa como:
    {"detail": <mensaje>, "error_code": <CODE>}
tal y como define docs/API_SPEC.md §8.
"""
from __future__ import annotations


class ApiError(Exception):
    """Error de negocio con status HTTP y error_code para el cliente."""

    status_code: int = 400
    error_code: str = "BAD_REQUEST"

    def __init__(
        self,
        detail: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


# ===== Autenticación / certificados (docs/API_SPEC.md §1) =====
class InvalidCertificateError(ApiError):
    status_code = 401
    error_code = "INVALID_CERT"


class CertificateExpiredError(ApiError):
    status_code = 401
    error_code = "CERT_EXPIRED"


class CertificateRevokedError(ApiError):
    status_code = 401
    error_code = "CERT_REVOKED"


class UntrustedIssuerError(ApiError):
    status_code = 401
    error_code = "UNTRUSTED_ISSUER"


class UnauthenticatedError(ApiError):
    status_code = 401
    error_code = "UNAUTHENTICATED"


class ForbiddenError(ApiError):
    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(ApiError):
    status_code = 404
    error_code = "NOT_FOUND"


class RateLimitError(ApiError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


# ===== Firma (docs/API_SPEC.md §3) =====
class SignatureInvalidError(ApiError):
    status_code = 400
    error_code = "SIGNATURE_INVALID"


class DocumentAlreadySignedError(ApiError):
    status_code = 400
    error_code = "DOCUMENT_ALREADY_SIGNED"


class CertificateInvalidError(ApiError):
    status_code = 400
    error_code = "CERTIFICATE_INVALID"


class TSAUnavailableError(ApiError):
    status_code = 503
    error_code = "TSA_UNAVAILABLE"


# ===== Workflows (docs/API_SPEC.md §4) =====
class InvalidSignerError(ApiError):
    status_code = 400
    error_code = "INVALID_SIGNER"


class WorkflowExistsError(ApiError):
    status_code = 409
    error_code = "WORKFLOW_EXISTS"
