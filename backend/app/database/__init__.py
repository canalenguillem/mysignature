"""Capa de acceso a datos: engine, sesiones y arranque del esquema."""
from app.database.connection import (
    SessionLocal,
    engine,
    get_db,
    get_mongodb,
    get_redis,
    mongodb,
    redis_client,
)
from app.models.base import Base


async def init_db() -> None:
    """Crea las tablas declaradas en los modelos si aún no existen.

    En desarrollo el esquema lo crea `init.sql` al arrancar MariaDB; este
    `create_all` (idempotente, checkfirst=True) sirve de red de seguridad y
    para entornos de test que levantan la BD en limpio.
    """
    # Importa los modelos para que queden registrados en el metadata.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "get_mongodb",
    "get_redis",
    "mongodb",
    "redis_client",
    "init_db",
]
