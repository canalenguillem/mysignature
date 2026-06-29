# API SPECIFICATION - ENDPOINTS REST

## Base URL

```
https://api.firma-digital.es/v1
```

## Autenticación

Todos los endpoints excepto `/auth/validate-cert` requieren:

```
Authorization: Bearer {JWT_TOKEN}
X-SSL-Client-Cert: {CERTIFICADO_PEM}  # Enviado por nginx
```

---

## 1. AUTENTICACIÓN

### POST /auth/validate-cert

Validar certificado digital y obtener JWT.

**Request:**
```json
{
  "certificate_pem": "-----BEGIN CERTIFICATE-----\nMIID...",
  "certificate_fingerprint": "abc123def456...",
  "subject": {
    "CN": "Juan Pérez García",
    "O": "Empresa S.L.",
    "C": "ES"
  },
  "issuer": {
    "O": "Fábrica Nacional de Moneda y Timbre",
    "CN": "FNMT RSA"
  },
  "serial_number": "123456789",
  "not_before": "2023-01-01T10:00:00Z",
  "not_after": "2025-01-01T10:00:00Z"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": 42,
    "cert_fingerprint": "abc123def456",
    "first_name": "Juan",
    "last_name": "Pérez García",
    "email": "juan@empresa.es"
  }
}
```

**Response (401):**
```json
{
  "detail": "Invalid certificate",
  "error_code": "INVALID_CERT"
}
```

**Posibles errores:**
- `INVALID_CERT` - Certificado no válido
- `CERT_EXPIRED` - Certificado expirado
- `CERT_REVOKED` - Certificado revocado
- `UNTRUSTED_ISSUER` - Emisor no reconocido
- `CERT_SIGNATURE_INVALID` - Firma del certificado inválida

---

### POST /auth/refresh

Refrescar access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

**Response (401):**
```json
{
  "detail": "Invalid refresh token"
}
```

---

### POST /auth/logout

Invalidar tokens.

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 2. DOCUMENTOS

### GET /documents

Listar documentos del usuario.

**Query Parameters:**
```
?status=pending_signatures  # pending, pending_signatures, fully_signed, archived
?limit=20
?offset=0
?sort=-created_at          # -created_at, -updated_at, title
```

**Response (200):**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Contrato de Servicios",
      "original_filename": "contrato.pdf",
      "status": "pending_signatures",
      "file_size": 245678,
      "owner": {
        "id": 42,
        "first_name": "Juan",
        "last_name": "Pérez"
      },
      "signatures_count": 1,
      "signatures_required": 3,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:20:00Z"
    }
  ]
}
```

---

### POST /documents

Subir nuevo documento PDF.

**Request:**
```
Content-Type: multipart/form-data

file: <PDF binary>
title: "Mi Contrato"
description: "Descripción opcional"
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Mi Contrato",
  "original_filename": "contrato.pdf",
  "file_size": 245678,
  "status": "pending",
  "owner_id": 42,
  "created_at": "2024-01-15T10:30:00Z",
  "message": "Document uploaded successfully"
}
```

**Response (400):**
```json
{
  "detail": "File must be PDF",
  "error_code": "INVALID_FILE_TYPE"
}
```

---

### GET /documents/{document_id}

Obtener detalles de un documento.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Mi Contrato",
  "original_filename": "contrato.pdf",
  "description": "Descripción del documento",
  "status": "fully_signed",
  "file_size": 245678,
  "content_hash": "sha256:abc123...",
  "owner": {
    "id": 42,
    "first_name": "Juan",
    "last_name": "Pérez"
  },
  "version": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z",
  "signatures": [
    {
      "id": 1001,
      "signer": {
        "id": 43,
        "first_name": "María",
        "last_name": "García"
      },
      "signed_at": "2024-01-15T11:00:00Z",
      "status": "signed"
    }
  ],
  "workflow": {
    "id": 5,
    "type": "parallel",
    "required_signers": 3,
    "completed_signers": 2,
    "status": "in_progress"
  }
}
```

---

### GET /documents/{document_id}/download

Descargar PDF (original o firmado).

**Query Parameters:**
```
?signed=true   # true: PDF con firmas, false: PDF original
```

**Response (200):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="contrato_signed.pdf"

<PDF binary data>
```

---

### DELETE /documents/{document_id}

Marcar documento como eliminado (soft delete).

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document deleted successfully"
}
```

**Response (403):**
```json
{
  "detail": "Cannot delete document with signatures"
}
```

---

## 3. FIRMAS

### POST /documents/{document_id}/sign

Enviar firma digital del documento.

**Request:**
```json
{
  "signature_base64": "MEUCIQDKZu0L1n...",
  "hash_algorithm": "SHA-256",
  "signature_algorithm": "RSA-PSS",
  "certificate_pem": "-----BEGIN CERTIFICATE-----\nMIID...",
  "certificate_fingerprint": "abc123def456"
}
```

**Backend Processing:**
1. Valida firma criptográficamente
2. Valida certificado del firmante
3. Obtiene timestamp de TSA
4. Embebe timestamp en PDF
5. Guarda PDF firmado en MongoDB
6. Registra en auditoría

**Response (200):**
```json
{
  "signature_id": 1001,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "signer_id": 43,
  "status": "signed",
  "signed_at": "2024-01-15T11:00:00Z",
  "tsa_timestamp": "2024-01-15T11:00:05Z",
  "tsa_authority": "http://tst.lacaixa.es",
  "message": "Document signed successfully"
}
```

**Response (400):**
```json
{
  "detail": "Invalid signature",
  "error_code": "SIGNATURE_INVALID"
}
```

**Posibles errores:**
- `SIGNATURE_INVALID` - Firma no válida
- `DOCUMENT_NOT_FOUND` - Documento no existe
- `DOCUMENT_ALREADY_SIGNED` - Ya está firmado
- `NOT_AUTHORIZED` - No tiene permiso para firmar
- `TSA_UNAVAILABLE` - Timestamp Authority no disponible
- `CERTIFICATE_INVALID` - Certificado inválido

---

### GET /documents/{document_id}/signatures

Obtener historial de firmas.

**Response (200):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_signatures": 2,
  "signatures": [
    {
      "id": 1001,
      "order": 1,
      "signer": {
        "id": 43,
        "first_name": "María",
        "last_name": "García",
        "cert_subject": {
          "CN": "María García",
          "O": "Empresa S.L."
        }
      },
      "signed_at": "2024-01-15T11:00:00Z",
      "signature_algorithm": "RSA-PSS",
      "hash_algorithm": "SHA-256",
      "tsa_timestamp": "2024-01-15T11:00:05Z",
      "tsa_authority": "http://tst.lacaixa.es",
      "status": "signed"
    },
    {
      "id": 1002,
      "order": 2,
      "signer": {
        "id": 44,
        "first_name": "Carlos",
        "last_name": "López"
      },
      "signed_at": "2024-01-15T14:30:00Z",
      "status": "signed"
    }
  ]
}
```

---

### POST /documents/{document_id}/signatures/{signature_id}/verify

Verificar que una firma es válida.

**Response (200):**
```json
{
  "signature_id": 1001,
  "valid": true,
  "details": {
    "certificate_valid": true,
    "signature_algorithm_valid": true,
    "timestamp_valid": true,
    "tsa_trusted": true
  }
}
```

---

## 4. WORKFLOWS DE FIRMA

### POST /documents/{document_id}/workflow

Crear flujo de firma colaborativa.

**Request:**
```json
{
  "signers": [
    {
      "cert_fingerprint": "xyz789...",
      "name": "María García",
      "email": "maria@empresa.es"
    },
    {
      "cert_fingerprint": "abc123...",
      "name": "Carlos López",
      "email": "carlos@empresa.es"
    }
  ],
  "type": "parallel",  # parallel o sequential
  "description": "Aprobación de contrato"
}
```

**Response (201):**
```json
{
  "workflow_id": 5,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "parallel",
  "required_signers": 2,
  "completed_signers": 0,
  "status": "pending",
  "assignments": [
    {
      "id": 501,
      "signer_cert_fingerprint": "xyz789...",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### GET /documents/{document_id}/workflow

Obtener estado del workflow.

**Response (200):**
```json
{
  "workflow_id": 5,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "parallel",
  "status": "in_progress",
  "required_signers": 2,
  "completed_signers": 1,
  "assignments": [
    {
      "id": 501,
      "signer": {
        "first_name": "María",
        "last_name": "García"
      },
      "status": "signed",
      "signed_at": "2024-01-15T11:00:00Z"
    },
    {
      "id": 502,
      "signer": {
        "first_name": "Carlos",
        "last_name": "López"
      },
      "status": "pending",
      "signed_at": null
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": null
}
```

---

### GET /auth/my-pending-signatures

Obtener documentos pendientes de firmar del usuario actual.

**Response (200):**
```json
{
  "total": 3,
  "pending_signatures": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Contrato de Servicios",
      "created_by": {
        "first_name": "Juan",
        "last_name": "Pérez"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "workflow": {
        "workflow_id": 5,
        "type": "parallel",
        "completed_signers": 1,
        "required_signers": 3
      }
    }
  ]
}
```

---

## 5. AUDITORÍA

### GET /documents/{document_id}/audit

Obtener log de auditoría completo de un documento.

**Query Parameters:**
```
?limit=50
?offset=0
?action=DOCUMENT_SIGNED  # DOCUMENT_UPLOADED, DOCUMENT_SIGNED, WORKFLOW_CREATED, etc.
```

**Response (200):**
```json
{
  "total": 12,
  "limit": 50,
  "offset": 0,
  "audit_logs": [
    {
      "id": 10001,
      "timestamp": "2024-01-15T10:30:00Z",
      "action": "DOCUMENT_UPLOADED",
      "actor": {
        "first_name": "Juan",
        "last_name": "Pérez",
        "cert_fingerprint": "abc123..."
      },
      "resource_type": "document",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000",
      "details": {
        "filename": "contrato.pdf",
        "size": 245678
      },
      "ip_address": "192.168.1.100",
      "success": true
    },
    {
      "id": 10002,
      "timestamp": "2024-01-15T11:00:00Z",
      "action": "DOCUMENT_SIGNED",
      "actor": {
        "first_name": "María",
        "last_name": "García",
        "cert_fingerprint": "xyz789..."
      },
      "resource_type": "document",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000",
      "details": {
        "signature_id": 1001,
        "algorithm": "RSA-PSS",
        "tsa_timestamp": "2024-01-15T11:00:05Z"
      },
      "ip_address": "192.168.1.101",
      "success": true
    }
  ]
}
```

---

### GET /audit/events

Búsqueda global de eventos de auditoría (solo admin).

**Query Parameters:**
```
?from=2024-01-01T00:00:00Z
?to=2024-01-31T23:59:59Z
?action=DOCUMENT_SIGNED
?severity=ERROR
?limit=100
```

**Response (200):**
```json
{
  "total": 456,
  "events": [
    {
      "id": 10001,
      "timestamp": "2024-01-15T11:00:00Z",
      "event_type": "DOCUMENT_SIGNED",
      "severity": "INFO",
      "message": "Document signed successfully",
      "metadata": {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "signer_id": 43
      }
    }
  ]
}
```

---

## 6. USUARIO ACTUAL

### GET /auth/me

Obtener información del usuario autenticado.

**Response (200):**
```json
{
  "id": 42,
  "cert_fingerprint": "abc123def456",
  "first_name": "Juan",
  "last_name": "Pérez García",
  "email": "juan@empresa.es",
  "cert_subject": {
    "CN": "Juan Pérez García",
    "O": "Empresa S.L.",
    "C": "ES"
  },
  "cert_issuer": {
    "O": "Fábrica Nacional de Moneda y Timbre",
    "CN": "FNMT RSA"
  },
  "cert_not_after": "2025-01-01T10:00:00Z",
  "is_active": true,
  "last_login": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-01T08:00:00Z"
}
```

---

## 7. BÚSQUEDA DE USUARIOS (Para Asignación de Firmas)

### GET /users/search

Buscar usuarios disponibles para asignar firmas en workflow.

**Query Parameters:**
```
?query=maria              # Búsqueda por email o nombre (case-insensitive)
?org=Empresa%20S.L.      # Filtrar por organización (opcional)
?limit=20
```

**Response (200):**
```json
{
  "total": 3,
  "results": [
    {
      "id": 43,
      "name": "María García López",
      "email": "maria@empresa.es",
      "organization": "Empresa S.L.",
      "cert_fingerprint": "xyz789...",
      "cert_expires": "2025-12-31T23:59:59Z",
      "cert_valid": true,
      "last_login": "2024-01-20T10:30:00Z"
    },
    {
      "id": 44,
      "name": "María García Pérez",
      "email": "maria.perez@empresa.es",
      "organization": "Empresa S.L.",
      "cert_fingerprint": "abc123...",
      "cert_expires": "2024-08-15T23:59:59Z",
      "cert_valid": false,
      "last_login": "2024-01-18T14:20:00Z"
    }
  ]
}
```

**Notas:**
- Solo retorna usuarios con al menos un login previo (que tengan certificado)
- `cert_valid: false` si certificado expiró (no seleccionable en frontend)
- Búsqueda es case-insensitive
- Limita a 20 resultados por defecto

---

### GET /users/by-organization/{organization}

Obtener todos los usuarios de una organización (útil para asignación masiva).

**Response (200):**
```json
{
  "organization": "Empresa S.L.",
  "total": 12,
  "users": [
    {
      "id": 43,
      "name": "María García",
      "email": "maria@empresa.es",
      "cert_valid": true,
      "cert_expires": "2025-12-31T23:59:59Z"
    },
    {
      "id": 44,
      "name": "Carlos López",
      "email": "carlos@empresa.es",
      "cert_valid": true,
      "cert_expires": "2025-06-30T23:59:59Z"
    }
  ]
}
```

---

## 8. ERRORES GLOBALES

### Response 401 - No Autenticado

```json
{
  "detail": "Not authenticated",
  "error_code": "UNAUTHENTICATED"
}
```

### Response 403 - No Autorizado

```json
{
  "detail": "Not authorized to perform this action",
  "error_code": "FORBIDDEN"
}
```

### Response 404 - No Encontrado

```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

### Response 422 - Validación Fallida

```json
{
  "detail": [
    {
      "loc": ["body", "certificate_pem"],
      "msg": "Invalid certificate format",
      "type": "value_error"
    }
  ]
}
```

### Response 500 - Error Interno

```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req_123456789"  # Para debugging
}
```

---

## 9. RATE LIMITING

Todos los endpoints están protegidos por rate limiting:

```
- /auth/validate-cert: 10 req/min por IP
- /documents: 100 req/min por usuario
- /documents/{id}/sign: 5 req/min por usuario
- /auth/refresh: 20 req/min por usuario
- /users/search: 50 req/min por usuario
```

**Response 429 - Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## 10. WEBHOOKS (Futuro)

```
POST https://tu-servidor.com/webhooks/firma-digital

Eventos:
- document.uploaded
- document.signed
- workflow.completed
- signature.rejected
```

---

## 11. VERSIONING

API sigue versionado semántico:
- `/v1` - Versión actual
- `/v2` - Próxima versión (en desarrollo)

Breaking changes requieren nueva versión.
