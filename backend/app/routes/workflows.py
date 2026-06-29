"""Rutas de workflows colaborativos (montadas bajo /api/v1/documents).

  POST /documents/{id}/workflow   -> crear workflow asignando firmantes
  GET  /documents/{id}/workflow   -> estado del workflow
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.workflow import (
    AssignmentCreated,
    AssignmentSigner,
    AssignmentStatus,
    WorkflowCreateRequest,
    WorkflowCreateResponse,
    WorkflowStatusResponse,
)
from app.security.jwt_handler import get_current_user
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("/{document_id}/workflow", response_model=WorkflowCreateResponse, status_code=201)
async def create_workflow(
    document_id: str,
    body: WorkflowCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowCreateResponse:
    document = DocumentService.get_document(db, document_id)
    workflow = WorkflowService.create_workflow(
        db=db,
        document=document,
        creator=current_user,
        signers=[s.model_dump() for s in body.signers],
        sequence_type=body.type,
        description=body.description,
    )

    await AuditService.log_action(
        db, "WORKFLOW_CREATED", current_user.id, "document", document_id, request,
        actor_cert_fingerprint=current_user.cert_fingerprint,
        details={"workflow_id": workflow.id, "type": workflow.sequence_type,
                 "required_signers": workflow.required_signers},
    )

    return WorkflowCreateResponse(
        workflow_id=workflow.id,
        document_id=document_id,
        type=workflow.sequence_type,
        required_signers=workflow.required_signers,
        completed_signers=workflow.completed_signers,
        status=workflow.status,
        assignments=[
            AssignmentCreated(
                id=a.id,
                signer_cert_fingerprint=a.signer_cert_fingerprint,
                status=a.status,
                sequence_number=a.sequence_number,
                created_at=a.created_at,
            )
            for a in workflow.assignments
        ],
        created_at=workflow.created_at,
    )


@router.get("/{document_id}/workflow", response_model=WorkflowStatusResponse)
async def get_workflow(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowStatusResponse:
    workflow = WorkflowService.get_workflow(db, document_id)
    return WorkflowStatusResponse(
        workflow_id=workflow.id,
        document_id=document_id,
        type=workflow.sequence_type,
        status=workflow.status,
        required_signers=workflow.required_signers,
        completed_signers=workflow.completed_signers,
        assignments=[
            AssignmentStatus(
                id=a.id,
                signer=AssignmentSigner.model_validate(a.signer),
                status=a.status,
                sequence_number=a.sequence_number,
                signed_at=a.signed_at,
            )
            for a in sorted(workflow.assignments, key=lambda x: x.sequence_number or x.id)
        ],
        created_at=workflow.created_at,
        completed_at=workflow.completed_at,
    )
