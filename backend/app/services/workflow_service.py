"""Workflows de firma colaborativa (paralela / secuencial).

Referencia: docs/ARCHITECTURE.md §Flujo 3 · docs/API_SPEC.md §4
            docs/IMPLEMENTATION_ORDER.md Tarea 5.2

Reglas (OPCIÓN 3 HÍBRIDA):
- Los firmantes deben existir (haberse autenticado) y tener certificado vigente.
- La validación del certificado se hace al CREAR el workflow.
- `parallel`: cualquiera firma en cualquier orden. `sequential`: por orden.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User
from app.models.workflow import SignatureWorkflow, WorkflowAssignment
from app.utils.errors import InvalidSignerError, NotFoundError, WorkflowExistsError
from app.utils.logger import logger


class WorkflowService:
    @staticmethod
    def create_workflow(
        db: Session,
        document: Document,
        creator: User,
        signers: List[dict],
        sequence_type: str = "parallel",
        description: str | None = None,
    ) -> SignatureWorkflow:
        if document.workflows:
            raise WorkflowExistsError("Document already has a workflow")

        if sequence_type not in ("parallel", "sequential"):
            raise InvalidSignerError("Invalid workflow type")

        # Resolver y validar firmantes por fingerprint.
        resolved: list[User] = []
        now = datetime.utcnow()
        for s in signers:
            fp = s.get("cert_fingerprint")
            user = db.query(User).filter(User.cert_fingerprint == fp).first()
            label = s.get("name") or s.get("email") or fp
            if user is None:
                raise InvalidSignerError(f"Signer not registered: {label}")
            if not user.cert_not_after or user.cert_not_after <= now:
                raise InvalidSignerError(f"Signer certificate expired: {label}")
            resolved.append(user)

        workflow = SignatureWorkflow(
            document_id=document.id,
            creator_id=creator.id,
            status="pending",
            required_signers=len(resolved),
            completed_signers=0,
            sequence_type=sequence_type,
        )
        db.add(workflow)
        db.flush()  # obtener workflow.id

        for idx, user in enumerate(resolved, start=1):
            db.add(
                WorkflowAssignment(
                    workflow_id=workflow.id,
                    signer_id=user.id,
                    signer_cert_fingerprint=user.cert_fingerprint,
                    status="pending",
                    sequence_number=idx if sequence_type == "sequential" else None,
                )
            )

        document.status = "pending_signatures"
        db.commit()
        db.refresh(workflow)
        logger.info(
            "Workflow %s creado doc=%s firmantes=%d tipo=%s",
            workflow.id, document.id, len(resolved), sequence_type,
        )
        return workflow

    @staticmethod
    def get_workflow(db: Session, document_id: str) -> SignatureWorkflow:
        workflow = (
            db.query(SignatureWorkflow)
            .filter(SignatureWorkflow.document_id == document_id)
            .order_by(SignatureWorkflow.id.desc())
            .first()
        )
        if workflow is None:
            raise NotFoundError("Workflow not found")
        return workflow

    @staticmethod
    def get_pending_for_user(db: Session, user: User) -> list[dict]:
        """Documentos con una asignación pendiente para `user`.

        En `sequential` solo se considera "desbloqueado" si todas las asignaciones
        con `sequence_number` menor ya están firmadas.
        """
        assignments = (
            db.query(WorkflowAssignment)
            .filter(
                WorkflowAssignment.signer_id == user.id,
                WorkflowAssignment.status == "pending",
            )
            .all()
        )

        pending: list[dict] = []
        for a in assignments:
            workflow = a.workflow
            if workflow is None or workflow.status in ("completed", "cancelled"):
                continue
            document = workflow.document
            if document is None or document.is_deleted:
                continue

            if workflow.sequence_type == "sequential" and a.sequence_number:
                earlier_pending = any(
                    o.sequence_number
                    and o.sequence_number < a.sequence_number
                    and o.status != "signed"
                    for o in workflow.assignments
                )
                if earlier_pending:
                    continue  # aún no es su turno

            pending.append({"assignment": a, "workflow": workflow, "document": document})
        return pending
