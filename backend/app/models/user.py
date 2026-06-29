"""Modelo User (MariaDB tabla `users`).

Referencia: docs/DATABASE.md §1.1 · docs/BACKEND_SPEC.md §app/models/user.py
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, JSON, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cert_fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    cert_subject = Column(JSON, nullable=False)
    cert_issuer = Column(JSON, nullable=False)
    cert_serial = Column(String(64))
    cert_not_before = Column(DateTime, nullable=False)
    cert_not_after = Column(DateTime, nullable=False)
    email = Column(String(255), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    organization = Column(String(255), index=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="owner")
    signatures = relationship("Signature", back_populates="signer")
    audit_logs = relationship("AuditLog", back_populates="actor")

    @property
    def full_name(self) -> str:
        return " ".join(p for p in [self.first_name, self.last_name] if p).strip()

    def __repr__(self) -> str:
        return f"<User {self.cert_fingerprint} ({self.full_name})>"
