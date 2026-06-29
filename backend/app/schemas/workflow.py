"""Schemas Pydantic para workflows de firma colaborativa.

Referencia: docs/API_SPEC.md §4
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Request =====
class SignerInput(BaseModel):
    cert_fingerprint: str
    name: Optional[str] = None
    email: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    signers: List[SignerInput] = Field(..., min_length=1)
    type: str = "parallel"  # parallel | sequential
    description: Optional[str] = None


# ===== Responses =====
class AssignmentCreated(BaseModel):
    id: int
    signer_cert_fingerprint: str
    status: str
    sequence_number: Optional[int] = None
    created_at: datetime


class WorkflowCreateResponse(BaseModel):
    workflow_id: int
    document_id: str
    type: str
    required_signers: int
    completed_signers: int
    status: str
    assignments: List[AssignmentCreated]
    created_at: datetime


class AssignmentSigner(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AssignmentStatus(BaseModel):
    id: int
    signer: AssignmentSigner
    status: str
    sequence_number: Optional[int] = None
    signed_at: Optional[datetime] = None


class WorkflowStatusResponse(BaseModel):
    workflow_id: int
    document_id: str
    type: str
    status: str
    required_signers: int
    completed_signers: int
    assignments: List[AssignmentStatus]
    created_at: datetime
    completed_at: Optional[datetime] = None


# ===== Pendientes de firma (GET /auth/my-pending-signatures) =====
class PendingWorkflowInfo(BaseModel):
    workflow_id: int
    type: str
    completed_signers: int
    required_signers: int


class PendingCreatedBy(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PendingSignatureItem(BaseModel):
    document_id: str
    title: str
    created_by: PendingCreatedBy
    created_at: datetime
    workflow: PendingWorkflowInfo


class PendingSignaturesResponse(BaseModel):
    total: int
    pending_signatures: List[PendingSignatureItem]
