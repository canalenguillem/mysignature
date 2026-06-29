"""Modelo Document (MariaDB tabla `documents`).

Referencia: docs/DATABASE.md §1.2
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base

DOCUMENT_STATUSES = (
    "pending",
    "pending_signatures",
    "fully_signed",
    "rejected",
    "archived",
)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)  # UUID
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    original_filename = Column(String(500), nullable=False)
    mongodb_id = Column(String(255), nullable=False)
    status = Column(Enum(*DOCUMENT_STATUSES, name="document_status"), default="pending")
    file_size = Column(BigInteger)
    content_hash = Column(String(64))
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="documents")
    signatures = relationship(
        "Signature", back_populates="document", cascade="all, delete-orphan"
    )
    workflows = relationship(
        "SignatureWorkflow", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.id} '{self.title}' ({self.status})>"
