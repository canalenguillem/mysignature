"""Modelos de auditoría (MariaDB tablas `audit_logs` y `audit_events`).

`audit_logs` es inmutable a nivel de BD (triggers en init.sql).
Referencia: docs/DATABASE.md §1.6 y §1.8
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False, index=True)
    actor_id = Column(BigInteger, ForeignKey("users.id"))
    actor_cert_fingerprint = Column(String(64), index=True)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    old_value = Column(JSON)
    new_value = Column(JSON)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} actor={self.actor_id} success={self.success}>"


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(100), index=True)
    severity = Column(
        Enum("INFO", "WARNING", "ERROR", "CRITICAL", name="audit_severity"), index=True
    )
    message = Column(Text)
    event_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AuditEvent {self.event_type} [{self.severity}]>"
