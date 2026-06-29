"""Conexiones a MariaDB (SQLAlchemy), MongoDB (PyMongo) y Redis.

Referencia: docs/BACKEND_SPEC.md §app/database/connection.py
"""
from typing import Generator

import redis
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# ===== MariaDB =====
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: sesión de BD por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== MongoDB =====
mongodb_client = MongoClient(settings.MONGODB_URL)
mongodb = mongodb_client[settings.MONGODB_DATABASE]


def get_mongodb():
    return mongodb


# ===== Redis =====
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis():
    return redis_client
