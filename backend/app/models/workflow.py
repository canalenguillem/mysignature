"""Modelos de workflow colaborativo.

Referencia: docs/DATABASE.md §1.4 (signature_workflows) y §1.5 (workflow_assignments)
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class SignatureWorkflow(Base):
    __tablename__ = "signature_workflows"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum("pending", "in_progress", "completed", "cancelled", name="workflow_status"),
        default="pending",
    )
    required_signers = Column(Integer, nullable=False)
    completed_signers = Column(Integer, default=0)
    sequence_type = Column(
        Enum("parallel", "sequential", name="workflow_sequence_type"),
        default="parallel",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    document = relationship("Document", back_populates="workflows")
    assignments = relationship(
        "WorkflowAssignment", back_populates="workflow", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SignatureWorkflow {self.id} doc={self.document_id} ({self.status})>"


class WorkflowAssignment(Base):
    __tablename__ = "workflow_assignments"
    __table_args__ = (
        UniqueConstraint("workflow_id", "signer_id", name="unique_assignment"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(
        BigInteger, ForeignKey("signature_workflows.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    signer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    signer_cert_fingerprint = Column(String(64), nullable=False)
    status = Column(
        Enum("pending", "signed", "rejected", name="assignment_status"),
        default="pending",
    )
    sequence_number = Column(Integer)
    signed_at = Column(DateTime)
    rejection_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("SignatureWorkflow", back_populates="assignments")
    signer = relationship("User")

    def __repr__(self) -> str:
        return f"<WorkflowAssignment wf={self.workflow_id} signer={self.signer_id} ({self.status})>"
