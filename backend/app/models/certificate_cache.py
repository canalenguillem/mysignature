"""Modelo CertificateCache (MariaDB tabla `certificate_cache`).

Referencia: docs/DATABASE.md §1.7
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    JSON,
    String,
    Text,
)

from app.models.base import Base


class CertificateCache(Base):
    __tablename__ = "certificate_cache"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    cert_pem = Column(Text, nullable=False)
    subject = Column(JSON)
    issuer = Column(JSON)
    serial = Column(String(64))
    not_before = Column(DateTime)
    not_after = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    validation_timestamp = Column(DateTime)
    revocation_status = Column(
        Enum("valid", "revoked", "unknown", name="revocation_status"),
        default="unknown",
    )
    last_revocation_check = Column(DateTime)
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CertificateCache {self.fingerprint} valid={self.is_valid}>"
