"""Re-exporta la factoría de sesiones para imports cómodos.

Referencia: docs/BACKEND_SPEC.md (estructura: database/session.py)
"""
from app.database.connection import SessionLocal, engine, get_db

__all__ = ["SessionLocal", "engine", "get_db"]
