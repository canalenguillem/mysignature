"""Registro de modelos SQLAlchemy.

Importar este paquete garantiza que todas las clases queden registradas en
`Base.metadata` (necesario para create_all y para resolver las relaciones por
nombre entre mappers).
"""
from app.models.audit_log import AuditEvent, AuditLog
from app.models.base import Base
from app.models.certificate_cache import CertificateCache
from app.models.document import Document
from app.models.signature import Signature
from app.models.user import User
from app.models.workflow import SignatureWorkflow, WorkflowAssignment

__all__ = [
    "Base",
    "User",
    "Document",
    "Signature",
    "SignatureWorkflow",
    "WorkflowAssignment",
    "AuditLog",
    "AuditEvent",
    "CertificateCache",
]
