# BASE DE DATOS - ESQUEMA Y DISEÑO

## Visión General

- **MariaDB**: Datos estructurados (usuarios, metadatos, auditoría, workflows)
- **MongoDB**: Documentos PDF (original, firmado, versiones)
- **Redis**: Sesiones, cache, colas

---

## 1. MARIADB - SCHEMA

### 1.1 Tabla: `users`

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cert_fingerprint VARCHAR(64) NOT NULL UNIQUE,
    cert_subject JSON NOT NULL,          -- {"CN": "Juan Pérez", "O": "..."}
    cert_issuer JSON NOT NULL,
    cert_serial VARCHAR(64),
    cert_not_before DATETIME NOT NULL,
    cert_not_after DATETIME NOT NULL,
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    organization VARCHAR(255),          -- Para filtrar por organización en búsqueda
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY unique_fingerprint (cert_fingerprint),
    INDEX idx_email (email),
    INDEX idx_organization (organization),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.2 Tabla: `documents`

```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,          -- UUID
    owner_id BIGINT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    original_filename VARCHAR(500) NOT NULL,
    mongodb_id VARCHAR(255) NOT NULL,    -- ObjectId en MongoDB
    status ENUM('pending', 'pending_signatures', 'fully_signed', 'rejected', 'archived') DEFAULT 'pending',
    file_size BIGINT,                    -- bytes
    content_hash VARCHAR(64),            -- SHA-256 del PDF original
    version INT DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_owner (owner_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.3 Tabla: `signatures`

```sql
CREATE TABLE signatures (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(36) NOT NULL,
    signer_id BIGINT NOT NULL,
    signer_cert_fingerprint VARCHAR(64) NOT NULL,
    signer_cert_subject JSON NOT NULL,
    signature_hash VARCHAR(64) NOT NULL,    -- SHA-256 de la firma
    signature_algorithm VARCHAR(50),        -- RSA-PSS, ECDSA, etc.
    hash_algorithm VARCHAR(50),             -- SHA-256, SHA-384, etc.
    tsa_response_base64 LONGTEXT,           -- RFC 3161 TimeStampToken
    tsa_timestamp DATETIME,                 -- Fecha del TSA
    tsa_authority VARCHAR(255),             -- URL del TSA
    signature_order INT,                    -- Orden si hay múltiples
    rejected BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    signed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (signer_id) REFERENCES users(id),
    UNIQUE KEY unique_signature (document_id, signer_id),
    INDEX idx_document (document_id),
    INDEX idx_signer (signer_id),
    INDEX idx_signed_at (signed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.4 Tabla: `signature_workflows`

```sql
CREATE TABLE signature_workflows (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(36) NOT NULL,
    creator_id BIGINT NOT NULL,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
    required_signers INT NOT NULL,
    completed_signers INT DEFAULT 0,
    sequence_type ENUM('parallel', 'sequential') DEFAULT 'parallel',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    PRIMARY KEY (id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES users(id),
    INDEX idx_document (document_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.5 Tabla: `workflow_assignments`

```sql
CREATE TABLE workflow_assignments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workflow_id BIGINT NOT NULL,
    signer_id BIGINT NOT NULL,
    signer_cert_fingerprint VARCHAR(64) NOT NULL,
    status ENUM('pending', 'signed', 'rejected') DEFAULT 'pending',
    sequence_number INT,                   -- Para workflows secuenciales
    signed_at DATETIME,
    rejection_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (workflow_id) REFERENCES signature_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (signer_id) REFERENCES users(id),
    UNIQUE KEY unique_assignment (workflow_id, signer_id),
    INDEX idx_workflow (workflow_id),
    INDEX idx_signer (signer_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.6 Tabla: `audit_logs` (INMUTABLE)

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100) NOT NULL,
    actor_id BIGINT,
    actor_cert_fingerprint VARCHAR(64),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    old_value JSON,
    new_value JSON,
    details JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (actor_id) REFERENCES users(id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_actor (actor_cert_fingerprint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Prevenir deletes (nivel DB)
ALTER TABLE audit_logs ADD CONSTRAINT no_delete_audit CHECK (1=1);
```

### 1.7 Tabla: `certificate_cache`

```sql
CREATE TABLE certificate_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    fingerprint VARCHAR(64) NOT NULL UNIQUE,
    cert_pem LONGTEXT NOT NULL,
    subject JSON,
    issuer JSON,
    serial VARCHAR(64),
    not_before DATETIME,
    not_after DATETIME,
    is_valid BOOLEAN DEFAULT TRUE,
    validation_timestamp DATETIME,
    revocation_status ENUM('valid', 'revoked', 'unknown') DEFAULT 'unknown',
    last_revocation_check DATETIME,
    expires_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY unique_fingerprint (fingerprint),
    INDEX idx_expires (expires_at),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.8 Tabla: `audit_events` (Para análisis)

```sql
CREATE TABLE audit_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    event_type VARCHAR(100),
    severity ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL'),
    message TEXT,
    metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_type (event_type),
    INDEX idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Migrations (Alembic)

```bash
# Estructura de carpetas
backend/app/database/migrations/
├── env.py
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_workflows.py
    └── 003_add_audit_events.py
```

---

## 2. MONGODB - SCHEMA

### 2.1 Colección: `documents`

```javascript
db.createCollection("documents", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "document_id", "original_pdf", "created_at"],
      properties: {
        _id: { bsonType: "objectId" },
        document_id: { bsonType: "string" },    // FK a documents.id en MariaDB
        original_pdf: { bsonType: "binData" },  // PDF original en binario
        signed_pdf: { bsonType: "binData" },    // PDF firmado (si existe)
        file_metadata: {
          bsonType: "object",
          properties: {
            filename: { bsonType: "string" },
            size: { bsonType: "int" },
            mime_type: { bsonType: "string" },
            pages: { bsonType: "int" }
          }
        },
        versions: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              version_number: { bsonType: "int" },
              pdf_data: { bsonType: "binData" },
              created_at: { bsonType: "date" },
              created_by_id: { bsonType: "long" }
            }
          }
        },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// Índices
db.documents.createIndex({ document_id: 1 }, { unique: true });
db.documents.createIndex({ created_at: -1 });
```

### 2.2 Colección: `signature_metadata`

```javascript
db.createCollection("signature_metadata", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "signature_id", "document_id"],
      properties: {
        _id: { bsonType: "objectId" },
        signature_id: { bsonType: "long" },     -- FK a signatures.id
        document_id: { bsonType: "string" },
        signer_cert_pem: { bsonType: "string" },
        signature_binary: { bsonType: "binData" },
        tsa_response_der: { bsonType: "binData" },
        timestamps: {
          bsonType: "object",
          properties: {
            signed_at: { bsonType: "date" },
            timestamp_from_tsa: { bsonType: "date" },
            audit_logged_at: { bsonType: "date" }
          }
        },
        algorithms: {
          bsonType: "object",
          properties: {
            signature_algorithm: { bsonType: "string" },
            hash_algorithm: { bsonType: "string" }
          }
        }
      }
    }
  }
});

db.signature_metadata.createIndex({ signature_id: 1 }, { unique: true });
db.signature_metadata.createIndex({ document_id: 1 });
db.signature_metadata.createIndex({ "timestamps.signed_at": -1 });
```

---

## 3. REDIS - ESTRUCTURA DE CLAVES

### Sesiones (JWT)

```redis
# Clave: "session:{token_jti}"
# Valor: { user_id, cert_fingerprint, expires_at }
# TTL: 15 minutos (access token)

session:abc123def456 {
  "user_id": 42,
  "cert_fingerprint": "abc123...",
  "iat": 1699564800,
  "exp": 1699565700
}

# TTL automático: Redis expira la clave después de expiración
```

### Refresh Tokens

```redis
# Clave: "refresh:{user_id}"
# Valor: { token, issued_at }
# TTL: 7 días

refresh:42 {
  "token": "xyz789...",
  "issued_at": 1699564800
}
```

### Cache de Certificados

```redis
# Clave: "cert:{fingerprint}"
# Valor: { pem, subject, issuer, valid_until }
# TTL: 24 horas

cert:abc123def456 {
  "pem": "-----BEGIN CERTIFICATE-----...",
  "subject": { "CN": "Juan Pérez" },
  "issuer": { "O": "FNMT" },
  "valid_until": 1699564800,
  "is_valid": true
}
```

### Cola de Firma (para procesar en background)

```redis
# Lista: "signing_queue"
# Elementos: { document_id, signer_id, signature_data }

RPUSH signing_queue '{"document_id":"uuid-1","signer_id":42,...}'
LPOP signing_queue  # Worker consume

# Worker procesa:
# - Valida firma
# - Obtiene timestamp TSA
# - Embebe en PDF
# - Actualiza estado en BD
```

### Rate Limiting

```redis
# Clave: "ratelimit:{ip}:{endpoint}"
# Valor: contador
# TTL: 60 segundos

ratelimit:192.168.1.1:/api/documents/sign 5/5
ratelimit:192.168.1.2:/api/documents/sign 3/5
```

---

## 4. RELACIONES Y INTEGRIDAD

### Diagrama de Relaciones

```
users (1) ──┬─→ (N) documents
            │    (owner_id)
            │
            ├─→ (N) signatures
            │    (signer_id)
            │
            └─→ (N) audit_logs
                 (actor_id)

documents (1) ──┬─→ (N) signatures
                ├─→ (N) signature_workflows
                └─→ (1) MongoDB (mongodb_id)

signature_workflows (1) ──→ (N) workflow_assignments

workflow_assignments (N) ──→ (1) signatures
```

### Integridad Referencial

```sql
-- Documento no puede ser eliminado si tiene firmas
ALTER TABLE documents ADD CONSTRAINT check_document_deletion
BEFORE DELETE ON documents FOR EACH ROW
BEGIN
  IF (SELECT COUNT(*) FROM signatures WHERE document_id = OLD.id) > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot delete document with signatures';
  END IF;
END;
```

---

## 5. ÍNDICES PARA PERFORMANCE

### Índices Estratégicos

```sql
-- Búsquedas rápidas por propietario
CREATE INDEX idx_documents_owner ON documents(owner_id, status, created_at DESC);

-- Auditoría por fecha rápida
CREATE INDEX idx_audit_logs_datetime ON audit_logs(timestamp DESC, action);

-- Firmas por documento
CREATE INDEX idx_signatures_document_signer ON signatures(document_id, signer_id);

-- Workflows
CREATE INDEX idx_workflows_document_status ON signature_workflows(document_id, status);

-- Cache de certificados
CREATE INDEX idx_cert_cache_validity ON certificate_cache(is_valid, expires_at);
```

---

## 6. BACKUP Y RECUPERACIÓN

### Estrategia de Backup

```bash
# MariaDB - Diario, full + incremental
00 02 * * * mysqldump --all-databases --single-transaction > /backups/mariadb-$(date +\%Y\%m\%d).sql

# MongoDB - Diario
00 03 * * * mongodump --out /backups/mongodb-$(date +\%Y\%m\%d)/

# Encriptar backups
find /backups -name "*.sql" -exec openssl enc -aes-256-cbc -salt -in {} -out {}.enc \;

# Enviar a almacenamiento externo (S3, etc)
aws s3 sync /backups s3://backup-bucket/firma-digital/ --delete
```

### Retención

- **Auditoría (audit_logs)**: 5 años mínimo
- **Documentos firmados**: 10 años (cumplimiento legal)
- **Backups incrementales**: 30 días
- **Backups completos**: 12 meses

---

## 7. MONITOREO

### Alertas en Producción

```yaml
# Prometheus/Alertmanager
- alert: MariaDB_High_Connections
  expr: mysql_global_status_threads_connected > 80
  for: 5m
  annotations:
    summary: "Conexiones altas en MariaDB"

- alert: MongoDB_Replication_Lag
  expr: mongodb_replication_oplog_tail_timestamp - on(instance) mongodb_replication_oplog_head_timestamp > 30

- alert: Audit_Log_Growth_Rate
  expr: rate(audit_logs_entries_total[1h]) > 1000
  annotations:
    summary: "Tasa inusual de eventos de auditoría"
```

---

## 8. DESARROLLO LOCAL

### Docker Compose Services

```yaml
mariadb:
  image: mariadb:10.5
  environment:
    MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    MYSQL_DATABASE: firma_digital
  ports:
    - "3306:3306"
  volumes:
    - mariadb_data:/var/lib/mysql
    - ./backend/app/database/init.sql:/docker-entrypoint-initdb.d/

mongodb:
  image: mongo:4.4
  ports:
    - "27017:27017"
  volumes:
    - mongodb_data:/data/db

redis:
  image: redis:6-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

---

## 9. SCRIPTS DE UTILIDAD

### Crear datos de prueba

```python
# backend/scripts/seed_data.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, Document
from datetime import datetime, timedelta

# Crear usuario de prueba con certificado fake
test_user = User(
    cert_fingerprint="abc123def456",
    cert_subject={"CN": "Test User", "O": "FNMT"},
    cert_issuer={"O": "FNMT", "CN": "FNMT Root"},
    cert_not_before=datetime.now() - timedelta(days=365),
    cert_not_after=datetime.now() + timedelta(days=365),
    email="test@example.com",
    first_name="Test",
    last_name="User"
)

# ... sesión y commit
```

---

## Referencias

- **MariaDB Best Practices**: https://mariadb.com/docs/
- **MongoDB Schema Design**: https://docs.mongodb.com/manual/core/schema-validation/
- **Redis Data Types**: https://redis.io/docs/data-types/
