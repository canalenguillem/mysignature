# BACKEND SPECIFICATION - FASTAPI + PYTHON

## Stack Tecnológico

```
Framework: FastAPI 0.100+
Language: Python 3.10+
Database ORM: SQLAlchemy 2.0+
Database: MariaDB 10.5+ con PyMySQL
NoSQL: MongoDB 4.4+ con PyMongo
Cache: Redis 6+ con redis-py
Cryptography: pyca/cryptography
JWT: python-jose
PDF: pypdf
HTTP Client: httpx (para TSA)
Testing: pytest + pytest-asyncio
```

---

## 1. ESTRUCTURA DEL PROYECTO

```
backend/
├── Dockerfile
├── requirements.txt
├── .env.example
├── pyproject.toml              # Config Poetry (opcional)
│
├── app/
│   ├── __init__.py
│   ├── main.py                # Entrada, configuración ASGI, middlewares
│   ├── config.py              # Variables de entorno, settings
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # Conexiones a BD
│   │   ├── session.py         # SessionLocal factory
│   │   └── migrations/        # Alembic
│   │       └── versions/
│   │           ├── 001_initial_schema.py
│   │           └── 002_workflows.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── signature.py
│   │   ├── audit_log.py
│   │   ├── workflow.py
│   │   ├── certificate_cache.py
│   │   └── base.py            # Base class para SQLAlchemy
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py            # Request/Response models Pydantic
│   │   ├── document.py
│   │   ├── signature.py
│   │   ├── workflow.py
│   │   └── audit.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── certificates.py    # Validación X.509, cadenas
│   │   ├── signature_validation.py  # Verificar firmas digitales
│   │   ├── tsa_client.py      # Cliente RFC 3161
│   │   ├── jwt_handler.py     # JWT tokens
│   │   └── revocation.py      # CRL/OCSP
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # POST /auth/*
│   │   ├── documents.py       # CRUD /documents
│   │   ├── signatures.py      # POST /sign, GET /audit
│   │   └── workflows.py       # Workflows colaborativos
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_service.py   # Lógica certificados
│   │   ├── document_service.py      # Gestión documentos
│   │   ├── signature_service.py     # Orquestación firma
│   │   ├── audit_service.py         # Log auditoría
│   │   ├── pdf_processor.py         # Validación/embedding PDF
│   │   ├── tsa_service.py           # Timestamp requests
│   │   └── workflow_service.py      # Workflows
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py          # Logging centralizado
│   │   ├── errors.py          # Excepciones custom
│   │   ├── decorators.py      # @require_auth, @audit, etc.
│   │   ├── formatters.py      # Formateo de datos
│   │   └── constants.py       # Constantes globales
│   │
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py            # Middleware autenticación
│       ├── audit.py           # Middleware auditoría
│       ├── security.py        # Headers de seguridad
│       └── error_handler.py   # Manejo de errores
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures pytest
│   ├── test_auth.py
│   ├── test_certificates.py
│   ├── test_signature_validation.py
│   ├── test_tsa_integration.py
│   └── test_documents.py
│
├── scripts/
│   ├── init_db.py             # Inicializar BD
│   ├── seed_data.py           # Datos de prueba
│   └── cleanup.py             # Limpieza
│
└── Makefile                    # Comandos útiles
```

---

## 2. ARCHIVOS CRÍTICOS

### app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, get_db
from app.routes import auth, documents, signatures, workflows
from app.middleware import auth_middleware, audit_middleware, security_headers
from app.utils import logger

# Event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicación...")
    await init_db()
    yield
    # Shutdown
    logger.info("Deteniendo aplicación...")

# Crear app
app = FastAPI(
    title="Firma Digital EIDAS",
    description="Plataforma de firma digital con certificados FNMT",
    version="1.0.0",
    lifespan=lifespan
)

# Middlewares de seguridad
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-SSL-Client-Cert"]
)

# Middlewares custom
app.add_middleware(security_headers.SecurityHeadersMiddleware)
app.add_middleware(audit_middleware.AuditMiddleware)
app.add_middleware(auth_middleware.AuthMiddleware)

# Rutas
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(signatures.router, prefix="/api/v1/signatures", tags=["signatures"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

### app/config.py

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    APP_NAME: str = "Firma Digital EIDAS"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost/firma_digital"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "firma_digital"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET: str  # Debe estar en .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    JWT_REFRESH_EXPIRATION_DAYS: int = 7
    
    # TSA (Timestamp Authority)
    TSA_URL: str = "http://tst.lacaixa.es"
    TSA_TIMEOUT: int = 30
    TSA_OID: str = "1.2.840.113549.1.9.16.2.14"  # id-signingCertificate
    
    # Certificados
    FNMT_ROOT_CA_PEM: str  # Path o contenido del certificado raíz FNMT
    CERTIFICATE_CACHE_TTL_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: List[str] = ["https://firma-digital.es"]
    ALLOWED_HOSTS: List[str] = ["firma-digital.es", "www.firma-digital.es"]
    
    # Seguridad
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf"]
    
    # Auditoría
    AUDIT_LOG_RETENTION_DAYS: int = 1825  # 5 años
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### app/database/connection.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
import redis
from app.config import settings

# MariaDB
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MongoDB
mongodb_client = MongoClient(settings.MONGODB_URL)
mongodb = mongodb_client[settings.MONGODB_DATABASE]

def get_mongodb():
    return mongodb

# Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis():
    return redis_client
```

---

## 3. MODELOS SQLALCHEMY

### app/models/user.py

```python
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    cert_fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    cert_subject = Column(JSON, nullable=False)
    cert_issuer = Column(JSON, nullable=False)
    cert_serial = Column(String(64))
    cert_not_before = Column(DateTime, nullable=False)
    cert_not_after = Column(DateTime, nullable=False)
    email = Column(String(255), unique=True, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    signatures = relationship("Signature", back_populates="signer")
    audit_logs = relationship("AuditLog", back_populates="actor")
    
    def __repr__(self):
        return f"<User {self.cert_fingerprint} ({self.first_name} {self.last_name})>"
```

### app/models/signature.py

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class Signature(Base):
    __tablename__ = "signatures"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    signer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    signer_cert_fingerprint = Column(String(64), nullable=False)
    signer_cert_subject = Column(JSON, nullable=False)
    signature_hash = Column(String(64), nullable=False)
    signature_algorithm = Column(String(50))  # RSA-PSS, ECDSA
    hash_algorithm = Column(String(50))       # SHA-256
    tsa_response_base64 = Column(LargeBinary)
    tsa_timestamp = Column(DateTime)
    tsa_authority = Column(String(255))
    signature_order = Column(Integer)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(String(500))
    signed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="signatures")
    signer = relationship("User", back_populates="signatures")
    
    def __repr__(self):
        return f"<Signature document={self.document_id} signer={self.signer_id}>"
```

---

## 4. SERVICIOS CRÍTICOS

### app/security/certificates.py

```python
from cryptography import x509
from cryptography.x509.oid import ExtensionOID, NameOID
from cryptography.hazmat.primitives import hashes
from datetime import datetime
import base64

class CertificateValidator:
    
    @staticmethod
    def validate_certificate_chain(cert_pem: str) -> dict:
        """
        Valida un certificado X.509 completo:
        1. Formato válido
        2. Fechas
        3. Uso de clave
        4. Emisor reconocido (FNMT)
        5. Revocación
        """
        
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
        except Exception as e:
            raise ValueError(f"Invalid certificate format: {str(e)}")
        
        # 1. Validar fechas
        now = datetime.utcnow()
        if not (cert.not_valid_before <= now <= cert.not_valid_after):
            raise ValueError("Certificate date is invalid")
        
        # 2. Validar issuer
        issuer_names = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if not any("Fábrica Nacional" in str(attr.value) or "FNMT" in str(attr.value) 
                   for attr in issuer_names):
            raise ValueError("Untrusted certificate issuer")
        
        # 3. Validar key usage
        try:
            key_usage = cert.extensions.get_extension_for_oid(
                ExtensionOID.KEY_USAGE
            ).value
            if not key_usage.digital_signature:
                raise ValueError("Certificate not authorized for digital signature")
        except x509.ExtensionNotFound:
            raise ValueError("Certificate missing key usage extension")
        
        # 4. Validar revocación
        is_revoked = CertificateValidator._check_revocation(cert)
        if is_revoked:
            raise ValueError("Certificate has been revoked")
        
        return {
            "valid": True,
            "subject": CertificateValidator._extract_subject(cert),
            "issuer": CertificateValidator._extract_issuer(cert),
            "serial_number": cert.serial_number,
            "not_before": cert.not_valid_before,
            "not_after": cert.not_valid_after,
            "fingerprint": CertificateValidator._calculate_fingerprint(cert_pem)
        }
    
    @staticmethod
    def _calculate_fingerprint(cert_pem: str) -> str:
        """Calcular SHA-256 fingerprint del certificado"""
        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        fingerprint = cert.fingerprint(hashes.SHA256())
        return fingerprint.hex().upper()
    
    @staticmethod
    def _extract_subject(cert: x509.Certificate) -> dict:
        """Extraer sujeto del certificado"""
        subject = {}
        for attr in cert.subject:
            oid_name = attr.oid._name
            subject[oid_name] = str(attr.value)
        return subject
    
    @staticmethod
    def _extract_issuer(cert: x509.Certificate) -> dict:
        """Extraer emisor del certificado"""
        issuer = {}
        for attr in cert.issuer:
            oid_name = attr.oid._name
            issuer[oid_name] = str(attr.value)
        return issuer
    
    @staticmethod
    def _check_revocation(cert: x509.Certificate) -> bool:
        """Validar revocación (OCSP/CRL)"""
        # TODO: Implementar OCSP/CRL check
        return False
```

### app/security/signature_validation.py

```python
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography import x509
import base64

class SignatureValidator:
    
    @staticmethod
    def verify_signature(
        pdf_bytes: bytes,
        signature_base64: str,
        certificate_pem: str
    ) -> bool:
        """
        Verifica que una firma digital es válida
        """
        
        try:
            # Decodificar firma
            signature_bytes = base64.b64decode(signature_base64)
            
            # Cargar certificado y extraer clave pública
            cert = x509.load_pem_x509_certificate(certificate_pem.encode())
            public_key = cert.public_key()
            
            # Calcular hash del PDF
            hash_digest = hashes.Hash(hashes.SHA256())
            hash_digest.update(pdf_bytes)
            pdf_hash = hash_digest.finalize()
            
            # Verificar firma según tipo de clave
            if isinstance(public_key, RSAPublicKey):
                public_key.verify(
                    signature_bytes,
                    pdf_hash,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            elif isinstance(public_key, EllipticCurvePublicKey):
                public_key.verify(signature_bytes, pdf_hash, ec.ECDSA(hashes.SHA256()))
            else:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
```

### app/security/tsa_client.py

```python
from datetime import datetime
import httpx
import base64
from asn1crypto import cms, tsp

class TSAClient:
    """
    Cliente RFC 3161 para obtener timestamp de Autoridad de Sellado de Tiempo
    """
    
    def __init__(self, tsa_url: str, timeout: int = 30):
        self.tsa_url = tsa_url
        self.timeout = timeout
    
    async def get_timestamp(self, data_hash: bytes) -> dict:
        """
        Solicitar timestamp a la TSA
        
        Args:
            data_hash: SHA-256 hash de los datos a sellar
        
        Returns:
            dict con timestamp response y detalles
        """
        
        # Crear TimeStampRequest (RFC 3161)
        tsr_request = self._create_timestamp_request(data_hash)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.tsa_url,
                content=tsr_request,
                headers={"Content-Type": "application/timestamp-query"}
            )
        
        if response.status_code != 200:
            raise Exception(f"TSA returned {response.status_code}")
        
        # Parsear TimeStampToken
        tst_token = response.content
        return self._parse_timestamp_response(tst_token)
    
    def _create_timestamp_request(self, data_hash: bytes) -> bytes:
        """Crear RFC 3161 TimeStampRequest"""
        # Usar librería asn1crypto para construir la request
        # ... implementación ...
        pass
    
    def _parse_timestamp_response(self, tst_token: bytes) -> dict:
        """Parsear RFC 3161 TimeStampToken"""
        # ... implementación ...
        return {
            "timestamp": datetime.utcnow(),
            "tst_base64": base64.b64encode(tst_token).decode(),
            "tsa_url": self.tsa_url
        }
```

### app/services/signature_service.py

```python
from sqlalchemy.orm import Session
from app.security.signature_validation import SignatureValidator
from app.security.tsa_client import TSAClient
from app.services.pdf_processor import PDFProcessor
from app.services.audit_service import AuditService
from app.utils.logger import logger

class SignatureService:
    
    @staticmethod
    async def sign_document(
        db: Session,
        document_id: str,
        signer_id: int,
        signature_base64: str,
        certificate_pem: str,
        certificate_fingerprint: str,
        request: Request
    ) -> dict:
        """
        Procesar firma de documento:
        1. Validar firma criptográfica
        2. Obtener timestamp de TSA
        3. Embeber timestamp en PDF
        4. Guardar PDF firmado en MongoDB
        5. Registrar en auditoría
        """
        
        try:
            # 1. Obtener documento y PDF original
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                raise ValueError("Document not found")
            
            pdf_bytes = PDFProcessor.get_document_bytes(document)
            
            # 2. Validar firma
            if not SignatureValidator.verify_signature(
                pdf_bytes,
                signature_base64,
                certificate_pem
            ):
                await AuditService.log_action(
                    db, "SIGNATURE_VALIDATION_FAILED", signer_id, 
                    "document", document_id, request
                )
                raise ValueError("Invalid signature")
            
            # 3. Obtener timestamp
            tsa_client = TSAClient(settings.TSA_URL)
            hash_obj = hashes.Hash(hashes.SHA256())
            hash_obj.update(pdf_bytes)
            data_hash = hash_obj.finalize()
            
            tsa_response = await tsa_client.get_timestamp(data_hash)
            
            # 4. Embeber timestamp en PDF (opcional en PDF)
            signed_pdf_bytes = PDFProcessor.embed_signature_metadata(
                pdf_bytes,
                signature_base64,
                certificate_pem,
                tsa_response["tst_base64"]
            )
            
            # 5. Guardar PDF en MongoDB
            mongodb = get_mongodb()
            mongodb_result = mongodb.documents.update_one(
                {"document_id": document_id},
                {"$set": {"signed_pdf": signed_pdf_bytes}}
            )
            
            # 6. Registrar firma en BD
            signature = Signature(
                document_id=document_id,
                signer_id=signer_id,
                signer_cert_fingerprint=certificate_fingerprint,
                signer_cert_subject=json.loads(certificate_pem),
                signature_hash=SignatureValidator.calculate_hash(signature_base64),
                signature_algorithm="RSA-PSS",
                hash_algorithm="SHA-256",
                tsa_response_base64=tsa_response["tst_base64"],
                tsa_timestamp=tsa_response["timestamp"],
                tsa_authority=settings.TSA_URL
            )
            db.add(signature)
            db.commit()
            
            # 7. Auditoría
            await AuditService.log_action(
                db, "DOCUMENT_SIGNED", signer_id,
                "document", document_id, request,
                details={
                    "signature_id": signature.id,
                    "algorithm": "RSA-PSS",
                    "tsa_timestamp": str(tsa_response["timestamp"])
                }
            )
            
            return {
                "signature_id": signature.id,
                "document_id": document_id,
                "signer_id": signer_id,
                "status": "signed",
                "signed_at": signature.signed_at.isoformat(),
                "tsa_timestamp": tsa_response["timestamp"].isoformat(),
                "tsa_authority": settings.TSA_URL
            }
        
        except Exception as e:
            logger.error(f"Signature error: {str(e)}")
            await AuditService.log_action(
                db, "SIGNATURE_ERROR", signer_id,
                "document", document_id, request,
                success=False,
                error_message=str(e)
            )
            raise
```

---

## 5. RUTAS

### app/routes/auth.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import CertificateValidationRequest, AuthResponse
from app.services.certificate_service import CertificateService
from app.database import get_db
from app.security.jwt_handler import create_access_token

router = APIRouter()

@router.post("/validate-cert", response_model=AuthResponse)
async def validate_certificate(
    request: CertificateValidationRequest,
    db: Session = Depends(get_db)
):
    """Validar certificado y obtener JWT"""
    
    try:
        # Validar certificado
        cert_data = CertificateService.validate_certificate_chain(
            request.certificate_pem
        )
        
        # Obtener o crear usuario
        user = db.query(User).filter(
            User.cert_fingerprint == cert_data["fingerprint"]
        ).first()
        
        if not user:
            user = User(
                cert_fingerprint=cert_data["fingerprint"],
                cert_subject=cert_data["subject"],
                cert_issuer=cert_data["issuer"],
                cert_not_before=cert_data["not_before"],
                cert_not_after=cert_data["not_after"],
                first_name=cert_data["subject"].get("CN", "").split()[0],
                email=cert_data["subject"].get("email")
            )
            db.add(user)
            db.commit()
        
        # Actualizar last_login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Generar tokens
        access_token = create_access_token(
            subject=str(user.id),
            expires_in=settings.JWT_EXPIRATION_MINUTES
        )
        refresh_token = create_refresh_token(user.id, db)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "cert_fingerprint": user.cert_fingerprint
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

### app/routes/signatures.py

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.schemas.signature import SignatureRequest
from app.services.signature_service import SignatureService
from app.security.jwt_handler import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("/documents/{document_id}/sign")
async def sign_document(
    document_id: str,
    signature_request: SignatureRequest,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Firmar documento con certificado digital"""
    
    try:
        result = await SignatureService.sign_document(
            db=db,
            document_id=document_id,
            signer_id=current_user.id,
            signature_base64=signature_request.signature_base64,
            certificate_pem=signature_request.certificate_pem,
            certificate_fingerprint=signature_request.certificate_fingerprint,
            request=request
        )
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 6. TESTING

### tests/test_certificates.py

```python
import pytest
from app.security.certificates import CertificateValidator

def test_validate_valid_certificate():
    """Test validación de certificado válido"""
    cert_pem = """-----BEGIN CERTIFICATE-----
    MIID...
    -----END CERTIFICATE-----"""
    
    result = CertificateValidator.validate_certificate_chain(cert_pem)
    assert result["valid"] == True
    assert result["fingerprint"]

def test_validate_expired_certificate():
    """Test certificado expirado"""
    # ... test
    pass

def test_validate_untrusted_issuer():
    """Test emisor no confiable"""
    # ... test
    pass
```

---

## 7. DOCKERFILE

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. REQUIREMENTS.TXT

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
cryptography==41.0.7
python-jose==3.3.0
pydantic==2.5.0
pydantic-settings==2.1.0
pymongo==4.6.0
redis==5.0.1
httpx==0.25.2
pypdf==4.0.1
asn1crypto==1.5.1
pkijs==1.1.14
pytest==7.4.3
pytest-asyncio==0.21.1
python-multipart==0.0.6
```

---

## Referencias

- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- pyca/cryptography: https://cryptography.io/
- RFC 3161: https://tools.ietf.org/html/rfc3161
