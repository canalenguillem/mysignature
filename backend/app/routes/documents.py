"""Rutas de documentos (CRUD).

Endpoints (docs/API_SPEC.md §2):
  POST   /documents                     -> subir PDF (multipart)
  GET    /documents                     -> listar (filtros + paginación)
  GET    /documents/{id}                -> detalle
  GET    /documents/{id}/download       -> descargar (original o firmado)
  DELETE /documents/{id}                -> soft delete
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.audit_service import AuditService
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
    OwnerInfo,
    SignatureBrief,
    SignerInfo,
    WorkflowBrief,
)
from app.security.jwt_handler import get_current_user
from app.services.document_service import DocumentService
from app.services.pdf_processor import PDFProcessor

router = APIRouter()


# ---------- helpers de serialización ----------
def _signature_status(sig) -> str:
    return "rejected" if sig.rejected else "signed"


def _to_list_item(db: Session, doc: Document) -> DocumentListItem:
    return DocumentListItem(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        status=doc.status,
        file_size=doc.file_size,
        owner=OwnerInfo.model_validate(doc.owner),
        signatures_count=len(doc.signatures),
        signatures_required=DocumentService.signatures_required(doc),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _to_detail(doc: Document) -> DocumentDetail:
    workflow = None
    if doc.workflows:
        wf = doc.workflows[0]
        workflow = WorkflowBrief(
            id=wf.id,
            type=wf.sequence_type,
            required_signers=wf.required_signers,
            completed_signers=wf.completed_signers,
            status=wf.status,
        )
    return DocumentDetail(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        description=doc.description,
        status=doc.status,
        file_size=doc.file_size,
        content_hash=doc.content_hash,
        owner=OwnerInfo.model_validate(doc.owner),
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        signatures=[
            SignatureBrief(
                id=s.id,
                signer=SignerInfo.model_validate(s.signer),
                signed_at=s.signed_at,
                status=_signature_status(s),
            )
            for s in doc.signatures
        ],
        workflow=workflow,
    )


# ---------- endpoints ----------
@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    file_bytes = await file.read()
    document = DocumentService.create_document(
        db=db,
        owner=current_user,
        file_bytes=file_bytes,
        title=title,
        original_filename=file.filename or "document.pdf",
        description=description,
        content_type=file.content_type,
    )
    await AuditService.log_action(
        db, "DOCUMENT_UPLOADED", current_user.id, "document", document.id, request,
        actor_cert_fingerprint=current_user.cert_fingerprint,
        details={"filename": document.original_filename, "size": document.file_size},
    )
    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        original_filename=document.original_filename,
        file_size=document.file_size,
        status=document.status,
        owner_id=document.owner_id,
        created_at=document.created_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("-created_at"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    result = DocumentService.list_documents(
        db=db, owner=current_user, status=status, limit=limit, offset=offset, sort=sort
    )
    return DocumentListResponse(
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        documents=[_to_list_item(db, d) for d in result["documents"]],
    )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDetail:
    document = DocumentService.get_document(db, document_id)
    return _to_detail(document)


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    signed: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    document = DocumentService.get_document(db, document_id)
    pdf_bytes = PDFProcessor.get_document_bytes(document, signed=signed)

    suffix = "_signed" if signed else ""
    base = document.original_filename.rsplit(".pdf", 1)[0]
    filename = f"{base}{suffix}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDeleteResponse:
    document = DocumentService.get_document(db, document_id)
    DocumentService.delete_document(db, document)
    await AuditService.log_action(
        db, "DOCUMENT_DELETED", current_user.id, "document", document_id, request,
        actor_cert_fingerprint=current_user.cert_fingerprint,
    )
    return DocumentDeleteResponse(id=document_id)
