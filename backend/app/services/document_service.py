"""Gestión de documentos: metadatos en MariaDB + binario en MongoDB.

Referencia: docs/IMPLEMENTATION_ORDER.md Tareas 3.3 y 3.5 · docs/API_SPEC.md §2
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from bson import Binary
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.signature import Signature
from app.models.user import User
from app.services.pdf_processor import PDFProcessor
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.logger import logger
from app.database.connection import get_mongodb

_SORT_FIELDS = {
    "-created_at": desc(Document.created_at),
    "created_at": Document.created_at,
    "-updated_at": desc(Document.updated_at),
    "updated_at": Document.updated_at,
    "title": Document.title,
}


class DocumentService:
    @staticmethod
    def create_document(
        db: Session,
        owner: User,
        file_bytes: bytes,
        title: str,
        original_filename: str,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Document:
        """Valida el PDF, guarda el binario en MongoDB y el metadato en MariaDB."""
        PDFProcessor.validate_pdf(file_bytes, content_type)
        info = PDFProcessor.get_pdf_info(file_bytes)
        content_hash = PDFProcessor.content_hash(file_bytes)

        document_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # 1. Binario + metadatos en MongoDB (colección documents).
        mongodb = get_mongodb()
        mongo_result = mongodb.documents.insert_one(
            {
                "document_id": document_id,
                "original_pdf": Binary(file_bytes),
                "file_metadata": {
                    "filename": original_filename,
                    "size": len(file_bytes),
                    "mime_type": content_type or "application/pdf",
                    "pages": info.pages,
                },
                "created_at": now,
                "updated_at": now,
            }
        )

        # 2. Metadato relacional en MariaDB.
        document = Document(
            id=document_id,
            owner_id=owner.id,
            title=title,
            description=description,
            original_filename=original_filename,
            mongodb_id=str(mongo_result.inserted_id),
            status="pending",
            file_size=len(file_bytes),
            content_hash=content_hash,
            version=1,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info("Documento creado id=%s owner=%s", document_id, owner.id)
        return document

    @staticmethod
    def get_document(db: Session, document_id: str, include_deleted: bool = False) -> Document:
        query = db.query(Document).filter(Document.id == document_id)
        if not include_deleted:
            query = query.filter(Document.is_deleted.is_(False))
        document = query.first()
        if document is None:
            raise NotFoundError("Document not found")
        return document

    @staticmethod
    def list_documents(
        db: Session,
        owner: User,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort: str = "-created_at",
    ) -> dict:
        query = db.query(Document).filter(
            Document.owner_id == owner.id,
            Document.is_deleted.is_(False),
        )
        if status:
            query = query.filter(Document.status == status)

        total = query.count()
        order = _SORT_FIELDS.get(sort, desc(Document.created_at))
        items = query.order_by(order).limit(limit).offset(offset).all()
        return {"total": total, "limit": limit, "offset": offset, "documents": items}

    @staticmethod
    def delete_document(db: Session, document: Document) -> None:
        """Soft delete. Bloquea si el documento ya tiene firmas (API_SPEC: 403)."""
        has_signatures = (
            db.query(Signature).filter(Signature.document_id == document.id).count() > 0
        )
        if has_signatures:
            raise ForbiddenError("Cannot delete document with signatures")

        document.is_deleted = True
        document.status = "archived"
        db.commit()
        logger.info("Documento marcado como eliminado id=%s", document.id)

    @staticmethod
    def signatures_required(document: Document) -> int:
        """Nº de firmantes requeridos según el workflow activo (0 si no hay)."""
        if document.workflows:
            return document.workflows[0].required_signers
        return 0
