"""Logging centralizado.

Referencia: docs/BACKEND_SPEC.md (estructura: utils/logger.py)
"""
import logging
import sys

from app.config import settings

_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO

logging.basicConfig(
    level=_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("firma_digital")
logger.setLevel(_LEVEL)

# Silenciar logs muy ruidosos de terceros (heartbeats de pymongo, watchfiles)
for _noisy in ("pymongo", "watchfiles", "httpcore", "httpx"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
