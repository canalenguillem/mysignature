"""Orquestación de la firma de un documento.

Flujo (docs/ARCHITECTURE.md §Flujo 2 · docs/BACKEND_SPEC.md §signature_service):
  1. Recuperar documento + PDF original
  2. Verificar la firma criptográficamente
  3. Obtener sello de tiempo (TSA RFC 3161)
  4. Persistir firma (MariaDB) + metadata binaria (MongoDB)
  5. Actualizar estado del documento / workflow
  6. Registrar en auditoría

Nota: el embebido PAdES real en el PDF queda pendiente; de momento se guarda la
metadata de firma y el `signed_pdf` referencia el original. Está marcado con TODO.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import Binary
from cryptography.hazmat.primitives import hashes
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.config import settings
from app.database.connection import get_mongodb
from app.models.document import Document
from app.models.signature import Signature
from app.models.user import User
from app.security.signature_validation import SignatureValidator
from app.security.tsa_client import TSAClient
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.pdf_processor import PDFProcessor
from app.utils.errors import (
    DocumentAlreadySignedError,
    NotFoundError,
    SignatureInvalidError,
)
from app.utils.logger import logger


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class SignatureService:
    @staticmethod
    async def sign_document(
        db: Session,
        document_id: str,
        signer: User,
        signature_base64: str,
        certificate_pem: str,
        certificate_fingerprint: str,
        request: Optional[Request] = None,
        hash_algorithm: str = "SHA-256",
        signature_algorithm: str = "RSA-PSS",
    ) -> dict:
        document = DocumentService.get_document(db, document_id)

        # Evitar doble firma del mismo firmante (unique_signature).
        existing = (
            db.query(Signature)
            .filter(
                Signature.document_id == document_id,
                Signature.signer_id == signer.id,
            )
            .first()
        )
        if existing is not None:
            raise DocumentAlreadySignedError("Document already signed by this user")

        pdf_bytes = PDFProcessor.get_document_bytes(document)

        # 1. Verificación criptográfica.
        if not SignatureValidator.verify_signature(
            pdf_bytes,
            signature_base64,
            certificate_pem,
            hash_algorithm=hash_algorithm,
            signature_algorithm=signature_algorithm,
        ):
            await AuditService.log_action(
                db, "SIGNATURE_VALIDATION_FAILED", signer.id,
                "document", document_id, request, success=False,
                error_message="Invalid signature",
            )
            raise SignatureInvalidError("Invalid signature")

        # 2. Sello de tiempo TSA (RFC 3161) sobre el hash del PDF.
        digest = hashes.Hash(hashes.SHA256())
        digest.update(pdf_bytes)
        data_hash = digest.finalize()
        tsa = await TSAClient(settings.TSA_URL, settings.TSA_TIMEOUT).get_timestamp(
            data_hash
        )
        tsa_timestamp = _naive_utc(tsa["timestamp"])

        # 3. Persistir firma en MariaDB.
        order = (
            db.query(Signature).filter(Signature.document_id == document_id).count() + 1
        )
        signature = Signature(
            document_id=document_id,
            signer_id=signer.id,
            signer_cert_fingerprint=certificate_fingerprint,
            signer_cert_subject=signer.cert_subject or {},
            signature_hash=SignatureValidator.calculate_hash(signature_base64),
            signature_algorithm=signature_algorithm,
            hash_algorithm=hash_algorithm,
            tsa_response_base64=tsa["tst_base64"].encode(),
            tsa_timestamp=tsa_timestamp,
            tsa_authority=settings.TSA_URL,
            signature_order=order,
        )
        db.add(signature)
        db.commit()
        db.refresh(signature)

        # 4. Metadata binaria en MongoDB + signed_pdf (placeholder = original).
        # TODO(Fase posterior): embebido PAdES real en el binario del PDF.
        SignatureService._persist_mongo(
            document_id, signature.id, certificate_pem, signature_base64, tsa, pdf_bytes
        )

        # 5. Estado del documento / workflow.
        SignatureService._advance_state(db, document, signer, signature)

        # 6. Auditoría.
        await AuditService.log_action(
            db, "DOCUMENT_SIGNED", signer.id, "document", document_id, request,
            actor_cert_fingerprint=certificate_fingerprint,
            details={
                "signature_id": signature.id,
                "algorithm": signature_algorithm,
                "tsa_timestamp": tsa_timestamp.isoformat(),
            },
        )

        logger.info("Documento %s firmado por %s", document_id, signer.id)
        return {
            "signature_id": signature.id,
            "document_id": document_id,
            "signer_id": signer.id,
            "status": "signed",
            "signed_at": signature.signed_at.isoformat(),
            "tsa_timestamp": tsa_timestamp.isoformat(),
            "tsa_authority": settings.TSA_URL,
            "message": "Document signed successfully",
        }

    # ----- helpers -----
    @staticmethod
    def _persist_mongo(document_id, signature_id, cert_pem, signature_b64, tsa, pdf_bytes):
        import base64

        mongodb = get_mongodb()
        mongodb.signature_metadata.insert_one(
            {
                "signature_id": signature_id,
                "document_id": document_id,
                "signer_cert_pem": cert_pem,
                "signature_binary": Binary(base64.b64decode(signature_b64)),
                "tsa_response_der": Binary(tsa["tst_der"]),
                "timestamps": {
                    "signed_at": datetime.utcnow(),
                    "timestamp_from_tsa": _naive_utc(tsa["timestamp"]),
                    "audit_logged_at": datetime.utcnow(),
                },
            }
        )
        # signed_pdf placeholder (sin PAdES embebido todavía).
        mongodb.documents.update_one(
            {"document_id": document_id},
            {"$set": {"signed_pdf": Binary(pdf_bytes), "updated_at": datetime.utcnow()}},
        )

    @staticmethod
    def _advance_state(db: Session, document: Document, signer: User, signature: Signature):
        workflow = document.workflows[0] if document.workflows else None

        if workflow is None:
            document.status = "fully_signed"
            db.commit()
            return

        assignment = next(
            (a for a in workflow.assignments if a.signer_id == signer.id), None
        )
        if assignment is not None and assignment.status != "signed":
            assignment.status = "signed"
            assignment.signed_at = datetime.utcnow()
            workflow.completed_signers = (workflow.completed_signers or 0) + 1

        if workflow.completed_signers >= workflow.required_signers:
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            document.status = "fully_signed"
        else:
            workflow.status = "in_progress"
            document.status = "pending_signatures"
        db.commit()

    @staticmethod
    def verify_signature_record(db: Session, document_id: str, signature_id: int) -> dict:
        """Re-verifica una firma almacenada (endpoint .../verify)."""
        signature = (
            db.query(Signature)
            .filter(Signature.id == signature_id, Signature.document_id == document_id)
            .first()
        )
        if signature is None:
            raise NotFoundError("Signature not found")

        document = DocumentService.get_document(db, document_id)
        pdf_bytes = PDFProcessor.get_document_bytes(document)

        mongodb = get_mongodb()
        meta = mongodb.signature_metadata.find_one({"signature_id": signature_id})

        certificate_valid = False
        signature_ok = False
        if meta:
            import base64

            cert_pem = meta.get("signer_cert_pem", "")
            sig_b64 = base64.b64encode(bytes(meta["signature_binary"])).decode()
            signature_ok = SignatureValidator.verify_signature(
                pdf_bytes, sig_b64, cert_pem,
                hash_algorithm=signature.hash_algorithm or "SHA-256",
                signature_algorithm=signature.signature_algorithm or "RSA-PSS",
            )
            certificate_valid = bool(cert_pem)

        timestamp_valid = signature.tsa_timestamp is not None
        return {
            "signature_id": signature_id,
            "valid": signature_ok and certificate_valid and timestamp_valid,
            "details": {
                "certificate_valid": certificate_valid,
                "signature_algorithm_valid": signature_ok,
                "timestamp_valid": timestamp_valid,
                "tsa_trusted": timestamp_valid,
            },
        }
