"""Rutas de firma (montadas bajo /api/v1/documents para casar con API_SPEC §3).

  POST /documents/{id}/sign
  GET  /documents/{id}/signatures
  POST /documents/{id}/signatures/{signature_id}/verify
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.signature import Signature
from app.models.user import User
from app.schemas.signature import (
    SignatureItem,
    SignaturesListResponse,
    SignatureRequest,
    SignerDetail,
    SignResponse,
    VerifyResponse,
)
from app.security.jwt_handler import get_current_user
from app.services.document_service import DocumentService
from app.services.signature_service import SignatureService

router = APIRouter()


def _status(sig: Signature) -> str:
    return "rejected" if sig.rejected else "signed"


@router.post("/{document_id}/sign", response_model=SignResponse)
async def sign_document(
    document_id: str,
    signature_request: SignatureRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignResponse:
    result = await SignatureService.sign_document(
        db=db,
        document_id=document_id,
        signer=current_user,
        signature_base64=signature_request.signature_base64,
        certificate_pem=signature_request.certificate_pem,
        certificate_fingerprint=signature_request.certificate_fingerprint,
        request=request,
        hash_algorithm=signature_request.hash_algorithm,
        signature_algorithm=signature_request.signature_algorithm,
    )
    return SignResponse(**result)


@router.get("/{document_id}/signatures", response_model=SignaturesListResponse)
async def list_signatures(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignaturesListResponse:
    document = DocumentService.get_document(db, document_id)
    sigs = sorted(document.signatures, key=lambda s: s.signature_order or s.id)
    return SignaturesListResponse(
        document_id=document_id,
        total_signatures=len(sigs),
        signatures=[
            SignatureItem(
                id=s.id,
                order=s.signature_order,
                signer=SignerDetail.model_validate(s.signer),
                signed_at=s.signed_at,
                signature_algorithm=s.signature_algorithm,
                hash_algorithm=s.hash_algorithm,
                tsa_timestamp=s.tsa_timestamp,
                tsa_authority=s.tsa_authority,
                status=_status(s),
            )
            for s in sigs
        ],
    )


@router.post(
    "/{document_id}/signatures/{signature_id}/verify",
    response_model=VerifyResponse,
)
async def verify_signature(
    document_id: str,
    signature_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerifyResponse:
    result = SignatureService.verify_signature_record(db, document_id, signature_id)
    return VerifyResponse(**result)
