"""Modelo Signature (MariaDB tabla `signatures`).

Referencia: docs/DATABASE.md §1.3 · docs/BACKEND_SPEC.md §app/models/signature.py
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class Signature(Base):
    __tablename__ = "signatures"
    __table_args__ = (
        UniqueConstraint("document_id", "signer_id", name="unique_signature"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    signer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    signer_cert_fingerprint = Column(String(64), nullable=False)
    signer_cert_subject = Column(JSON, nullable=False)
    signature_hash = Column(String(64), nullable=False)
    signature_algorithm = Column(String(50))  # RSA-PSS, ECDSA
    hash_algorithm = Column(String(50))        # SHA-256
    tsa_response_base64 = Column(LargeBinary)
    tsa_timestamp = Column(DateTime)
    tsa_authority = Column(String(255))
    signature_order = Column(Integer)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(Text)
    signed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="signatures")
    signer = relationship("User", back_populates="signatures")

    def __repr__(self) -> str:
        return f"<Signature document={self.document_id} signer={self.signer_id}>"
