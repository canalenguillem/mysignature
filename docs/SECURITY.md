# SEGURIDAD Y COMPLIANCE - FIRMA DIGITAL EIDAS

## Resumen Ejecutivo

Esta plataforma maneja operaciones criptográficas con datos sensibles (certificados, firmas digitales). La seguridad es **NO NEGOCIABLE**. Este documento es una checklist de implementación.

---

## 1. CRIPTOGRAFÍA

### Algoritmos Permitidos

#### Firma Digital
- ✅ **RSA-PSS** con SHA-256 (RECOMENDADO)
  - Parámetros: RSA-2048 mínimo, salt length = SHA-256 output length
- ✅ **ECDSA** con SHA-256 (si el certificado lo soporta)
  - Parámetros: P-256 mínimo

#### Hashing
- ✅ **SHA-256** (RECOMENDADO para PDF)
- ✅ **SHA-384** (aceptable)
- ❌ **MD5, SHA-1** (prohibidos)

#### Encriptación (en tránsito)
- ✅ **TLS 1.3** (RECOMENDADO)
- ✅ **TLS 1.2** (aceptable, con cipher suites modernos)
- ❌ TLS 1.0, 1.1, SSL 3.0

#### Encriptación (en reposo - opcional)
- Si se almacenan datos sensibles en BD
- ✅ **AES-256-GCM**

### Implementación en Código

**Frontend (Web Crypto API)**
```typescript
// Algoritmo de firma
const algorithm = {
  name: "RSA-PSS",
  saltLength: 32  // SHA-256 output length
};

// Algoritmo de hash
const hash = "SHA-256";

// Importar clave pública del certificado
const publicKey = await crypto.subtle.importKey(
  "spki",
  derBuffer,
  algorithm,
  false,
  ["verify"]
);

// Firmar (se hace en el cert del navegador, no en Frontend)
const signature = await crypto.subtle.sign(
  algorithm,
  privateKey,  // Solo accesible desde cert del navegador
  bufferToSign
);
```

**Backend (pyca/cryptography)**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Verificar firma
public_key.verify(
    signature_bytes,
    data_to_verify,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)
```

---

## 2. AUTENTICACIÓN Y AUTORIZACIÓN

### Autenticación: Certificados TLS Mutuos

1. **Cliente presenta certificado X.509**
   - Durante handshake TLS
   - El navegador usa el certificado FNMT instalado
   - No se requiere password adicional

2. **Servidor valida certificado**
   ```python
   # En FastAPI middleware
   client_cert = request.headers.get("X-SSL-Client-Cert")
   # Validar X.509, cadena, fechas, revocación
   ```

3. **Backend genera JWT**
   ```python
   payload = {
       "sub": certificate_fingerprint,  # Identificador único
       "iss": "firma-digital-app",
       "aud": "api.firma-digital.es",
       "exp": datetime.utcnow() + timedelta(minutes=15),
       "cert_subject": certificate.subject
   }
   token = create_access_token(payload)
   ```

### Autorización: JWT + Roles

- **Access Token**: Expiración 15 minutos
- **Refresh Token**: Expiración 7 días (almacenado en DB)
- **Roles**: user, admin

```python
@router.post("/documents/{id}/sign")
async def sign_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # get_current_user extrae y valida JWT
    # Verifica que user actual es dueño del documento o tiene permiso
    document = db.query(Document).filter(Document.id == id).first()
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
```

---

## 3. VALIDACIÓN DE CERTIFICADOS X.509

### En Frontend (validación básica)

```typescript
// certificateService.ts
export async function validateCertificateBasic(cert: Certificate) {
  const now = new Date();
  
  // 1. Validar fechas
  if (now < cert.notBefore || now > cert.notAfter) {
    throw new Error("Certificado expirado o no válido aún");
  }
  
  // 2. Validar uso de clave (debe incluir digitalSignature)
  if (!cert.keyUsage.includes("digitalSignature")) {
    throw new Error("Certificado no autorizado para firma");
  }
  
  // 3. Validar extensiones críticas
  const hasSignatureExt = cert.extensions.some(
    e => e.oid === "2.5.29.19" // basicConstraints
  );
  
  return {
    valid: true,
    subject: cert.subject,
    issuer: cert.issuer,
    serialNumber: cert.serialNumber
  };
}
```

### En Backend (validación completa)

```python
# security/certificates.py
from cryptography import x509
from cryptography.x509.oid import ExtensionOID, NameOID
import pyopenssl

def validate_certificate_chain(cert_pem: str, issuer_pem: str = None):
    """
    Valida:
    1. Formato X.509 correcto
    2. Cadena de certificados
    3. Fechas válidas
    4. Revocación (CRL/OCSP)
    5. Emisor reconocido (FNMT)
    """
    
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    
    # 1. Validar fechas
    now = datetime.utcnow()
    if not (cert.not_valid_before < now < cert.not_valid_after):
        raise CertificateExpired("Certificado expirado")
    
    # 2. Validar emisor
    issuer = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
    if not any("Fábrica Nacional" in str(i.value) for i in issuer):
        raise InvalidIssuer("Certificado no emitido por FNMT")
    
    # 3. Validar uso de clave
    key_usage = cert.extensions.get_extension_for_oid(
        ExtensionOID.KEY_USAGE
    )
    if not key_usage.value.digital_signature:
        raise InvalidKeyUsage("No autorizado para firma digital")
    
    # 4. Validar revocación
    is_revoked = check_revocation_status(cert)
    if is_revoked:
        raise CertificateRevoked("Certificado ha sido revocado")
    
    return True
```

### Revocación (CRL/OCSP)

```python
# security/certificates.py
def check_revocation_status(cert: x509.Certificate) -> bool:
    """
    Intenta OCSP primero (más rápido), luego CRL
    """
    
    # 1. OCSP (Online Certificate Status Protocol)
    ocsp_url = get_ocsp_url_from_cert(cert)
    if ocsp_url:
        try:
            status = check_ocsp(cert, ocsp_url)
            return status == "revoked"
        except:
            pass  # Fallback a CRL
    
    # 2. CRL (Certificate Revocation List)
    crl_urls = get_crl_urls_from_cert(cert)
    for crl_url in crl_urls:
        try:
            crl_data = requests.get(crl_url, timeout=5).content
            crl = x509.load_der_x509_crl(crl_data)
            
            for revoked_cert in crl:
                if revoked_cert.serial_number == cert.serial_number:
                    return True
        except:
            continue
    
    return False
```

---

## 4. VALIDACIÓN DE FIRMAS DIGITALES

### En Backend

```python
# security/signature_validation.py
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def validate_pdf_signature(
    pdf_bytes: bytes,
    signature_base64: str,
    cert_pem: str
) -> dict:
    """
    Valida que la firma digital es correcta
    """
    
    # 1. Decodificar firma
    signature_bytes = base64.b64decode(signature_base64)
    
    # 2. Cargar certificado y extraer clave pública
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    public_key = cert.public_key()
    
    # 3. Calcular hash del PDF
    hash_digest = hashes.Hash(hashes.SHA256())
    hash_digest.update(pdf_bytes)
    pdf_hash = hash_digest.finalize()
    
    # 4. Verificar firma
    try:
        public_key.verify(
            signature_bytes,
            pdf_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return {"valid": True, "message": "Firma válida"}
    except InvalidSignature:
        return {"valid": False, "message": "Firma inválida"}
```

---

## 5. PROTECCIÓN DE DATOS EN TRÁNSITO

### HTTPS/TLS Obligatorio

**En nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    
    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    
    # TLS 1.3 (recomendado) + 1.2
    ssl_protocols TLSv1.3 TLSv1.2;
    
    # Cipher suites modernos
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # Forzar HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### Certificados TLS Mutuos (mTLS)

```nginx
# Requerir certificado cliente
ssl_client_certificate /etc/nginx/certs/ca.crt;
ssl_verify_client on;
ssl_verify_depth 2;

# Pasar certificado al backend
proxy_set_header X-SSL-Client-Cert $ssl_client_cert;
proxy_set_header X-SSL-Client-Verify $ssl_client_verify;
```

---

## 6. PROTECCIÓN DE DATOS EN REPOSO

### Estructura de Carpetas

```
/certs/
  ├── ca.crt              # Raíz FNMT (público)
  ├── server.crt          # Certificado servidor (público)
  ├── server.key          # Clave servidor (PRIVADA, permisos 0600)
  └── .gitignore          # NO commitear claves
```

### En Docker

```dockerfile
# No copiar claves privadas en imagen
COPY certs/server.crt /etc/nginx/certs/
# server.key se monta como volume secreto en docker-compose.yml
```

### En docker-compose.yml

```yaml
secrets:
  server_key:
    file: ./certs/server.key
    
services:
  nginx:
    secrets:
      - server_key
    volumes:
      - type: bind
        source: /run/secrets/server_key
        target: /etc/nginx/certs/server.key
        read_only: true
```

### Datos Sensibles en BD

Si necesitas almacenar datos sensibles:

```python
from cryptography.fernet import Fernet

# En config.py
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY)

# Encriptar antes de guardar
encrypted_data = cipher.encrypt(sensitive_data.encode())
db.add(Document(encrypted_field=encrypted_data))

# Desencriptar al recuperar
decrypted_data = cipher.decrypt(db_document.encrypted_field).decode()
```

---

## 7. AUDITORÍA E INMUTABILIDAD

### Tabla de Auditoría (MariaDB)

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50) NOT NULL,
    actor_cert_fingerprint VARCHAR(64) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSON,
    ip_address VARCHAR(45),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_actor (actor_cert_fingerprint),
    CONSTRAINT audit_logs_no_delete CHECK (1=1)  -- Prevenir deletes
) ENGINE=InnoDB;
```

### Implementación en Backend

```python
# services/audit_service.py
async def log_action(
    db: Session,
    action: str,
    actor: str,  # Fingerprint del certificado
    resource_type: str,
    resource_id: str,
    details: dict,
    request: Request
):
    log = AuditLog(
        action=action,
        actor_cert_fingerprint=actor,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host
    )
    db.add(log)
    db.commit()

# En endpoint de firma
@router.post("/documents/{id}/sign")
async def sign_document(
    id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... lógica de firma ...
    
    await audit_service.log_action(
        db,
        action="DOCUMENT_SIGNED",
        actor=current_user.cert_fingerprint,
        resource_type="document",
        resource_id=id,
        details={"algorithm": "RSA-PSS", "hash": "SHA-256"},
        request=request
    )
```

---

## 8. CONTROL DE ACCESO

### Autenticación: Solo Certificado

```python
# routes/auth.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        cert_fingerprint = payload.get("sub")
        
        # Validar que el certificado sigue siendo válido
        user = db.query(User).filter(
            User.cert_fingerprint == cert_fingerprint
        ).first()
        
        if not user:
            raise HTTPException(status_code=401)
        
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Autorización: Propietario del Documento

```python
@router.post("/documents/{id}/sign")
async def sign_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == id).first()
    
    # Solo el propietario o asignado puede firmar
    if (document.owner_id != current_user.id and 
        current_user.id not in document.assigned_signers):
        raise HTTPException(status_code=403, detail="No permission")
    
    # ... lógica ...
```

---

## 9. HEADERS DE SEGURIDAD

**En FastAPI:**
```python
# main.py
from fastapi.middleware import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["firma-digital.es", "www.firma-digital.es"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://firma-digital.es"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

---

## 10. RATE LIMITING

```python
# main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/documents/{id}/sign")
@limiter.limit("5/minute")  # 5 firmas por minuto por IP
async def sign_document(request: Request, ...):
    # ...
```

---

## 11. VALIDACIÓN DE ENTRADA

```python
# schemas/signature.py
from pydantic import BaseModel, validator

class SignatureRequest(BaseModel):
    document_id: str
    signature_base64: str
    certificate_pem: str
    
    @validator("signature_base64")
    def validate_signature_format(v):
        try:
            base64.b64decode(v)
        except:
            raise ValueError("Signature must be valid base64")
        return v
    
    @validator("certificate_pem")
    def validate_certificate_format(v):
        if not v.startswith("-----BEGIN CERTIFICATE-----"):
            raise ValueError("Invalid certificate format")
        try:
            x509.load_pem_x509_certificate(v.encode())
        except:
            raise ValueError("Invalid certificate")
        return v
```

---

## 12. LOGGING SEGURO

```python
# utils/logger.py
import logging

# NO loguear datos sensibles
logger = logging.getLogger(__name__)

handler = logging.FileHandler("/var/log/firma-digital/app.log")
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# En código
logger.info(f"User signed document")  # ✓ Bien
logger.info(f"Signature: {signature}")  # ✗ MAL - loguea datos sensibles
```

---

## 13. CHECKLIST DE DESPLIEGUE

- [ ] TLS 1.3+ configurado
- [ ] Certificados TLS válidos y no autofirmados
- [ ] CORS restringido a dominios específicos
- [ ] Rate limiting habilitado
- [ ] Logs auditados sin datos sensibles
- [ ] JWT secrets en variables de entorno (.env)
- [ ] Claves privadas NUNCA en git
- [ ] Validación de certificados cliente habilitada
- [ ] TSA configurada y probada
- [ ] Tabla de auditoría con permisos de solo inserción
- [ ] Backups de BD encriptados
- [ ] Monitoreo de intentos de acceso fallidos
- [ ] Política de retención de logs (90 días mínimo)

---

## 14. REFERENCIAS NORMATIVAS

- **EIDAS (Reglamento UE 910/2014)**
  - Artículo 26: Firma Avanzada
  - Artículo 41: Servicio de Timestamp
  
- **ETSI TS 101 733** - AdES (Advanced Electronic Signatures)
  
- **OWASP Top 10** - Aplicable a seguridad web

---

## Contacto de Seguridad

Para reportar vulnerabilidades: security@firma-digital.es

NO publicar vulnerabilidades en GitHub issues.
