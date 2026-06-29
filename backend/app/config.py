"""Configuración central de la aplicación (variables de entorno).

Referencia: docs/BACKEND_SPEC.md §app/config.py
"""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    APP_NAME: str = "Firma Digital EIDAS"

    # Database
    DATABASE_URL: str = "mysql+pymysql://firma_user:change_me_secure_password@localhost:3306/firma_digital"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "firma_digital"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET: str = "dev_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # TSA (Timestamp Authority)
    TSA_URL: str = "http://tst.lacaixa.es"
    TSA_TIMEOUT: int = 30
    TSA_OID: str = "1.2.840.113549.1.9.16.2.14"  # id-signingCertificate

    # Certificados
    FNMT_ROOT_CA_PEM: str = ""  # Path o contenido del certificado raíz FNMT
    CERTIFICATE_CACHE_TTL_HOURS: int = 24

    # CORS / Hosts (en dev se permite el front de Vite y localhost)
    CORS_ORIGINS: List[str] = [
        "https://firma-digital.es",
        "http://localhost:5173",
        "http://localhost",
    ]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Seguridad
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf"]

    # Rate limiting de /auth (req por minuto y por IP)
    AUTH_RATE_LIMIT_PER_MIN: int = 10

    # Auditoría
    AUDIT_LOG_RETENTION_DAYS: int = 1825  # 5 años

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
