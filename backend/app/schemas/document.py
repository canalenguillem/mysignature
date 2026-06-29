"""Schemas Pydantic para documentos.

Referencia: docs/API_SPEC.md §2
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OwnerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# ===== Upload =====
class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    file_size: Optional[int] = None
    status: str
    owner_id: int
    created_at: datetime
    message: str = "Document uploaded successfully"


# ===== List =====
class DocumentListItem(BaseModel):
    id: str
    title: str
    original_filename: str
    status: str
    file_size: Optional[int] = None
    owner: OwnerInfo
    signatures_count: int = 0
    signatures_required: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    documents: List[DocumentListItem]


# ===== Detail =====
class SignerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class SignatureBrief(BaseModel):
    id: int
    signer: SignerInfo
    signed_at: datetime
    status: str


class WorkflowBrief(BaseModel):
    id: int
    type: str
    required_signers: int
    completed_signers: int
    status: str


class DocumentDetail(BaseModel):
    id: str
    title: str
    original_filename: str
    description: Optional[str] = None
    status: str
    file_size: Optional[int] = None
    content_hash: Optional[str] = None
    owner: OwnerInfo
    version: int
    created_at: datetime
    updated_at: datetime
    signatures: List[SignatureBrief] = []
    workflow: Optional[WorkflowBrief] = None


class DocumentDeleteResponse(BaseModel):
    id: str
    message: str = "Document deleted successfully"
