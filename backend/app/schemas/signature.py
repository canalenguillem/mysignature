"""Schemas Pydantic para firmas.

Referencia: docs/API_SPEC.md §3
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ===== Request =====
class SignatureRequest(BaseModel):
    signature_base64: str
    hash_algorithm: str = "SHA-256"
    signature_algorithm: str = "RSA-PSS"
    certificate_pem: str
    certificate_fingerprint: str


# ===== Responses =====
class SignResponse(BaseModel):
    signature_id: int
    document_id: str
    signer_id: int
    status: str
    signed_at: str
    tsa_timestamp: Optional[str] = None
    tsa_authority: Optional[str] = None
    message: str = "Document signed successfully"


class SignerDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    cert_subject: Optional[dict] = None


class SignatureItem(BaseModel):
    id: int
    order: Optional[int] = None
    signer: SignerDetail
    signed_at: datetime
    signature_algorithm: Optional[str] = None
    hash_algorithm: Optional[str] = None
    tsa_timestamp: Optional[datetime] = None
    tsa_authority: Optional[str] = None
    status: str


class SignaturesListResponse(BaseModel):
    document_id: str
    total_signatures: int
    signatures: List[SignatureItem]


class VerifyDetails(BaseModel):
    certificate_valid: bool
    signature_algorithm_valid: bool
    timestamp_valid: bool
    tsa_trusted: bool


class VerifyResponse(BaseModel):
    signature_id: int
    valid: bool
    details: VerifyDetails
