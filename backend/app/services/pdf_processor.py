"""Validación y procesado de PDFs.

Referencia: docs/IMPLEMENTATION_ORDER.md Tarea 3.2 · docs/BACKEND_SPEC.md (pdf_processor)
Librería: pypdf
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import settings
from app.database.connection import get_mongodb
from app.utils.errors import ApiError, NotFoundError
from app.utils.logger import logger

_PDF_MAGIC = b"%PDF"


class InvalidFileTypeError(ApiError):
    status_code = 400
    error_code = "INVALID_FILE_TYPE"


class FileTooLargeError(ApiError):
    status_code = 400
    error_code = "FILE_TOO_LARGE"


@dataclass
class PDFInfo:
    pages: int
    title: str
    author: str
    producer: str


class PDFProcessor:
    """Operaciones sobre el binario PDF (no embebe firmas: eso va en Fase 4)."""

    @staticmethod
    def validate_pdf(file_bytes: bytes, content_type: str | None = None) -> None:
        """Valida tipo MIME, tamaño y cabecera mágica `%PDF`."""
        if content_type and content_type not in settings.ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError("File must be PDF")

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise FileTooLargeError(
                f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes"
            )

        if not file_bytes[:4] == _PDF_MAGIC:
            raise InvalidFileTypeError("Invalid PDF file")

        # Comprobar que pypdf puede abrirlo.
        try:
            PdfReader(_to_stream(file_bytes))
        except (PdfReadError, Exception) as exc:  # noqa: BLE001
            raise InvalidFileTypeError(f"Invalid PDF file: {exc}") from exc

    @staticmethod
    def get_pdf_info(file_bytes: bytes) -> PDFInfo:
        """Extrae metadatos del PDF."""
        reader = PdfReader(_to_stream(file_bytes))
        meta = reader.metadata or {}
        return PDFInfo(
            pages=len(reader.pages),
            title=(meta.get("/Title") or "Sin título"),
            author=(meta.get("/Author") or "Desconocido"),
            producer=(meta.get("/Producer") or ""),
        )

    @staticmethod
    def content_hash(file_bytes: bytes) -> str:
        """SHA-256 hex del PDF original."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def get_document_bytes(document, signed: bool = False) -> bytes:
        """Recupera el binario del PDF (original o firmado) desde MongoDB."""
        mongodb = get_mongodb()
        doc = mongodb.documents.find_one({"document_id": document.id})
        if not doc:
            raise NotFoundError("Document binary not found")

        key = "signed_pdf" if signed else "original_pdf"
        data = doc.get(key)
        if data is None:
            if signed:
                raise NotFoundError("Signed PDF not available")
            raise NotFoundError("Original PDF not available")
        return bytes(data)


def _to_stream(file_bytes: bytes):
    import io

    return io.BytesIO(file_bytes)
