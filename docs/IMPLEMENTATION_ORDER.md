# IMPLEMENTATION ORDER - GUÍA DE CONSTRUCCIÓN

## Resumen Ejecutivo

Este documento define el **orden recomendado** para construir el proyecto en fases, con dependencias claras entre componentes.

**Duración estimada**: 12-16 semanas (equipos de 2-3 desarrolladores)

---

## FASE 1: INFRAESTRUCTURA (Semana 1-2)

Objetivo: Tener toda la infraestructura en funcionamiento.

### Tarea 1.1: Setup del Proyecto

```bash
# 1. Crear estructura base
mkdir -p firma-digital-eidas
cd firma-digital-eidas

# 2. Git initialization
git init
git remote add origin <tu-repo>

# 3. Crear carpetas principales
mkdir -p backend frontend nginx certs
mkdir -p backend/app/{database,models,routes,services,security,utils}
mkdir -p frontend/src/{components,services,hooks,pages,types,utils}

# 4. .gitignore
echo "
.env
.env.local
*.pyc
__pycache__/
node_modules/
dist/
.vscode/
.idea/
certs/
.DS_Store
" > .gitignore
```

**Deliverables:**
- ✅ Estructura de carpetas completa
- ✅ Repositorio git inicializado
- ✅ .gitignore configurado

---

### Tarea 1.2: Docker Compose Setup

Implementar:
- ✅ `docker-compose.yml` (desarrollo)
- ✅ `docker-compose.prod.yml` (producción)
- ✅ `.env.example`
- ✅ Makefile

**Archivos a crear:**
```
docker-compose.yml
docker-compose.prod.yml
.env.example
Makefile
```

**Testing:**
```bash
cp .env.example .env
make build
make up
make ps  # Verificar que todos los servicios están running
```

---

### Tarea 1.3: Database Initialization

Crear:
- ✅ `backend/app/database/connection.py` (conexiones)
- ✅ `backend/app/database/session.py` (SessionLocal)
- ✅ `backend/app/database/init.sql` (script de inicialización)

**Testing:**
```bash
docker-compose exec mariadb mysql -u firma_user -p firma_digital -e "SHOW TABLES;"
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec redis redis-cli ping
```

---

## FASE 2: BACKEND - AUTENTICACIÓN (Semana 3-4)

Objetivo: Usuarios pueden autenticarse con certificado digital.

### Tarea 2.1: Modelos SQLAlchemy

```python
# backend/app/models/
- base.py (Base class)
- user.py (User model)
```

**Testing:**
```bash
docker-compose exec backend python -c "
from app.models import User
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

---

### Tarea 2.2: Validación de Certificados X.509

Implementar:
- ✅ `backend/app/security/certificates.py`
  - `CertificateValidator.validate_certificate_chain()`
  - `CertificateValidator._extract_subject()`
  - `CertificateValidator._extract_issuer()`
  - `CertificateValidator._calculate_fingerprint()`

**Librerías necesarias:**
```
cryptography>=41.0.7
pyopenssl>=23.3.0
```

**Testing:**
```python
from app.security.certificates import CertificateValidator

# Crear certificado de prueba
cert_pem = "-----BEGIN CERTIFICATE-----\n..."

result = CertificateValidator.validate_certificate_chain(cert_pem)
assert result["valid"] == True
```

---

### Tarea 2.3: JWT Handler

Implementar:
- ✅ `backend/app/security/jwt_handler.py`
  - `create_access_token()`
  - `create_refresh_token()`
  - `decode_token()`
  - `get_current_user()` (Depends)

**Testing:**
```bash
# Generar token de prueba
docker-compose exec backend python -c "
from app.security.jwt_handler import create_access_token
token = create_access_token('test@example.com')
print(f'Token: {token}')
"
```

---

### Tarea 2.4: Auth Routes

Implementar:
- ✅ `backend/app/routes/auth.py`
  - `POST /auth/validate-cert`
  - `POST /auth/refresh`
  - `POST /auth/logout`
  - `GET /auth/me`

- ✅ `backend/app/schemas/auth.py` (Pydantic models)

**Testing:**
```bash
# Probar endpoints
curl -X POST http://localhost:8000/api/v1/auth/validate-cert \
  -H "Content-Type: application/json" \
  -d '{"certificate_pem":"..."}'
```

---

### Tarea 2.5: Middleware de Autenticación

Implementar:
- ✅ `backend/app/middleware/auth.py`
  - Validar JWT en cada request
  - Extraer usuario actual
  - Rate limiting en `/auth`

**Testing:**
```bash
# Endpoint protegido sin token debe retornar 401
curl http://localhost:8000/api/v1/documents
# Response: 401 Unauthorized
```

---

## FASE 3: BACKEND - GESTIÓN DE DOCUMENTOS (Semana 5-6)

Objetivo: Usuarios pueden subir y listar documentos PDF.

### Tarea 3.1: Modelos de Documentos

```python
# backend/app/models/
- document.py (Document model)
```

**Schema:**
- Incluir MongoDB ObjectId reference
- Status enum

---

### Tarea 3.2: Validación de PDFs

Implementar:
- ✅ `backend/app/services/pdf_processor.py`
  - `validate_pdf()`
  - `get_pdf_info()`
  - `get_document_bytes()`

**Librerías:**
```
pypdf>=4.0.1
```

---

### Task 3.3: Servicio de Documentos

Implementar:
- ✅ `backend/app/services/document_service.py`
  - `create_document()`
  - `get_document()`
  - `list_documents()`
  - `delete_document()`

---

### Tarea 3.4: Routes de Documentos

Implementar:
- ✅ `backend/app/routes/documents.py`
  - `POST /documents` (upload)
  - `GET /documents` (list)
  - `GET /documents/{id}` (detail)
  - `GET /documents/{id}/download`
  - `DELETE /documents/{id}`

- ✅ `backend/app/schemas/document.py`

**Testing:**
```bash
# Upload PDF
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@test.pdf" \
  -F "title=Mi Documento"

# List documents
curl http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer TOKEN"
```

---

### Tarea 3.5: MongoDB Integration

- ✅ Almacenar PDFs en MongoDB (collection `documents`)
- ✅ Índices apropiados
- ✅ Validación de schema

---

## FASE 4: BACKEND - FIRMA DIGITAL (Semana 7-8)

Objetivo: Usuarios pueden firmar PDFs digitalmente.

### Tarea 4.1: Validación de Firmas

Implementar:
- ✅ `backend/app/security/signature_validation.py`
  - `verify_signature()` (verificar firma criptográficamente)
  - `verify_pdf_signature()`

**Testing:**
```python
from app.security.signature_validation import SignatureValidator

# Verificar que una firma es válida
is_valid = SignatureValidator.verify_signature(
    pdf_bytes=pdf_data,
    signature_base64=sig,
    certificate_pem=cert
)
assert is_valid == True
```

---

### Tarea 4.2: TSA Client (RFC 3161)

Implementar:
- ✅ `backend/app/security/tsa_client.py`
  - `get_timestamp()` (solicitar a TSA)
  - `_create_timestamp_request()`
  - `_parse_timestamp_response()`

**Librerías:**
```
asn1crypto>=1.5.1
```

**Testing:**
```bash
# Probar con TSA de CaixaBank (desarrollo)
docker-compose exec backend python -c "
import asyncio
from app.security.tsa_client import TSAClient

tsa = TSAClient('http://tst.lacaixa.es')
result = asyncio.run(tsa.get_timestamp(b'test_hash'))
print(result)
"
```

---

### Tarea 4.3: Servicio de Firma

Implementar:
- ✅ `backend/app/services/signature_service.py`
  - `sign_document()` (orquestación completa)
  - Validar firma
  - Obtener timestamp
  - Guardar en MongoDB
  - Registrar en auditoría

---

### Tarea 4.4: Routes de Firma

Implementar:
- ✅ `backend/app/routes/signatures.py`
  - `POST /documents/{id}/sign`
  - `GET /documents/{id}/signatures`
  - `POST /documents/{id}/signatures/{sig_id}/verify`

- ✅ `backend/app/schemas/signature.py`

**Testing:**
```bash
# Firmar documento
curl -X POST http://localhost:8000/api/v1/documents/uuid/sign \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signature_base64":"...",
    "certificate_pem":"...",
    "hash_algorithm":"SHA-256"
  }'
```

---

### Tarea 4.5: Modelos de Firma y Auditoría

```python
# backend/app/models/
- signature.py (Signature model)
- audit_log.py (AuditLog model)
```

---

## FASE 5: BACKEND - WORKFLOWS Y AUDITORÍA (Semana 9)

Objetivo: Soporte para firma colaborativa y auditoría completa.

### Tarea 5.1: Modelos de Workflows

```python
# backend/app/models/
- workflow.py (Workflow y WorkflowAssignment models)
```

---

### Tarea 5.2: Servicio de Workflows + Búsqueda de Usuarios

Implementar:
- ✅ `backend/app/services/workflow_service.py`
  - `create_workflow()` (crear workflow con validación de signers)
  - `assign_signers()` (asignar firmantes)
  - `get_workflow_status()` (estado actual)
  - Marcar como completado cuando todas las firmas están
  
- ✅ `backend/app/routes/users.py` (NUEVO)
  - `GET /users/search` (buscar usuarios por email/nombre con certs vigentes)
  - `GET /users/by-organization/{org}` (obtener usuarios por organización)
  
**Decisión arquitectónica: OPCIÓN 3 HÍBRIDA**
- Búsqueda por email/nombre (case-insensitive)
- Solo usuarios con certificados vigentes
- Filtro opcional por organización
- Validación de certificado al crear workflow (no al firmar)

---

### Tarea 5.3: Routes de Workflows

Implementar:
- ✅ `backend/app/routes/workflows.py`
  - `POST /documents/{id}/workflow` (crear workflow asignando signers)
  - `GET /documents/{id}/workflow` (ver estado workflow)
  - `GET /auth/my-pending-signatures` (documentos pendientes del usuario)
  - Validar que todos los signers tienen certs vigentes

---

### Tarea 5.4: Auditoría

Implementar:
- ✅ `backend/app/services/audit_service.py`
  - `log_action()` (registrar cada operación)

- ✅ `backend/app/middleware/audit.py`
  - Middleware que registra automáticamente

- ✅ `backend/app/routes/audit.py` (opcional para admin)
  - `GET /documents/{id}/audit`
  - `GET /audit/events`

---

## FASE 6: FRONTEND - BASE (Semana 10)

Objetivo: Estructura base del frontend React + autenticación.

### Tarea 6.1: Setup Vite + React

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install axios react-router-dom
```

**Estructura:**
- ✅ `src/main.tsx`
- ✅ `src/App.tsx`
- ✅ `vite.config.ts`
- ✅ `tsconfig.json`

---

### Tarea 6.2: Types TypeScript

Implementar:
- ✅ `src/types/certificate.ts`
- ✅ `src/types/document.ts`
- ✅ `src/types/signature.ts`
- ✅ `src/types/workflow.ts`

---

### Tarea 6.3: Services

Implementar:
- ✅ `src/services/apiService.ts` (axios + interceptors)
- ✅ `src/services/storageService.ts` (localStorage/sessionStorage)
- ✅ `src/services/certificateService.ts` (parsing de certificados)

**Librerías:**
```
npm install axios pkijs asn1js @noble/hashes
```

---

### Tarea 6.4: Auth Context y Hooks

Implementar:
- ✅ `src/context/AuthContext.tsx`
- ✅ `src/hooks/useAuth.ts`
- ✅ `src/hooks/useCertificate.ts`

---

### Tarea 6.5: Login Page

Implementar:
- ✅ `src/pages/LoginPage.tsx`
  - Solicitar certificado del navegador
  - Validar certificado localmente
  - Enviar al backend para obtener JWT
  - Guardar tokens

**Componentes:**
- ✅ `src/components/Auth/CertificateValidator.tsx`
- ✅ `src/components/Auth/CertificateInfo.tsx`

---

## FASE 7: FRONTEND - DOCUMENTOS (Semana 11)

Objetivo: Usuarios pueden subir y listar documentos.

### Tarea 7.1: Dashboard Page

Implementar:
- ✅ `src/pages/DashboardPage.tsx`
  - Lista de documentos
  - Filtros (status, fecha, etc.)

---

### Tarea 7.2: Upload Component

Implementar:
- ✅ `src/components/DocumentUpload/PDFUploader.tsx`
  - Validar PDF en cliente
  - Mostrar preview
  - Upload al servidor

- ✅ `src/hooks/useDocument.ts`
- ✅ `src/services/pdfService.ts`

**Librerías:**
```
npm install pdf-lib
```

---

### Tarea 7.3: Document Detail Page

Implementar:
- ✅ `src/pages/DocumentDetailPage.tsx`
  - Mostrar metadatos
  - Preview del PDF
  - Historial de firmas
  - Botón "Descargar"

---

## FASE 8: FRONTEND - FIRMA (Semana 12)

Objetivo: Usuarios pueden firmar documentos.

### Tarea 8.1: Crypto Service

Implementar:
- ✅ `src/services/cryptoService.ts`
  - `hashSHA256()`
  - `signData()`
  - `verifySignature()`

**Nota:** El navegador maneja la firma usando el certificado instalado.

---

### Tarea 8.2: Signature Components

Implementar:
- ✅ `src/components/SignaturePanel/SignatureForm.tsx`
  - Botón "Firmar"
  - Estados (signing, success, error)

- ✅ `src/components/SignaturePanel/SignatureVerification.tsx`
  - Resumen antes de firmar

- ✅ `src/components/SignaturePanel/SignatureResult.tsx`
  - Resultado de la firma

- ✅ `src/hooks/useSignature.ts`

---

### Tarea 8.3: Audit Log Component

Implementar:
- ✅ `src/components/AuditLog/AuditViewer.tsx`
  - Tabla de eventos
  - Timeline de firmas

- ✅ `src/pages/AuditPage.tsx`

---

## FASE 9: FRONTEND - WORKFLOWS (Semana 13)

Objetivo: Interfaz para firma colaborativa con búsqueda y asignación de usuarios.

### Tarea 9.1: Workflow Components con Búsqueda de Usuarios

Implementar:
- ✅ `src/components/WorkflowPanel/WorkflowCreator.tsx`
  - Input de búsqueda (email/nombre)
  - Resultados: usuarios con certs vigentes
  - Mostrar expiración de certificado
  - Seleccionar múltiples usuarios
  - Radio buttons: Paralela vs Secuencial
  - Validar certificados antes de crear workflow

- ✅ `src/components/WorkflowPanel/SignerAssignment.tsx` (NUEVO)
  - Búsqueda rápida de usuarios
  - Mostrar estado del certificado (✓ válido / ✗ expirado)
  - Agregar/remover usuarios de lista
  - Orden de firma (si es secuencial)

- ✅ `src/components/WorkflowPanel/WorkflowViewer.tsx`
  - Ver estado del workflow
  - Mostrar quién ha firmado
  - Mostrar quién está pendiente
  - Indicar si es paralela o secuencial

- ✅ `src/components/WorkflowPanel/PendingSignatures.tsx`
  - Documentos pendientes del usuario
  - Filtrar por estado (pendiente, en progreso)

- ✅ `src/hooks/useWorkflow.ts`
  - Crear workflow con validación
  - Buscar usuarios
  - Obtener estado del workflow

**Decisión: OPCIÓN 3 HÍBRIDA - Búsqueda por Email/Nombre**
- Input busca por email o nombre (case-insensitive)
- Backend retorna solo usuarios con certificados vigentes
- Frontend valida `cert_valid: true` antes de permitir selección
- Mostrar organización del usuario (opcional filtro)
- Al crear workflow, validar que todos los signers tienen certs vigentes

---

### Tarea 9.2: Pending Signatures Page

Implementar:
- ✅ `src/pages/PendingSignaturesPage.tsx`
  - Dashboard de firmas pendientes
  - Quick-sign desde aquí
  - Mostrar quien más debe firmar (paralela/secuencial)
  - Ordenar por fecha de creación

---

## FASE 10: TESTING Y QA (Semana 14-15)

Objetivo: Asegurar calidad y coverage.

### Tarea 10.1: Backend Testing

```bash
# Tests unitarios
docker-compose exec backend pytest tests/

# Coverage
docker-compose exec backend pytest --cov=app tests/
```

**Mínimo 80% coverage:**
- ✅ `tests/test_certificates.py`
- ✅ `tests/test_signature_validation.py`
- ✅ `tests/test_tsa_integration.py`
- ✅ `tests/test_documents.py`
- ✅ `tests/test_auth.py`

---

### Tarea 10.2: Frontend Testing

```bash
# Tests unitarios
npm run test

# E2E (Playwright o Cypress)
npm run test:e2e
```

---

### Tarea 10.3: Security Audit

Checklist:
- [ ] OWASP Top 10 review
- [ ] Validación de entrada en todos los endpoints
- [ ] Sanitización de salida
- [ ] SQL injection tests
- [ ] CORS misconfiguration
- [ ] Certificado TLS válido
- [ ] Rate limiting funcional
- [ ] Headers de seguridad correctos

---

## FASE 11: DEPLOYMENT Y DOCUMENTACIÓN (Semana 16)

Objetivo: Preparar para producción.

### Tarea 11.1: Producción Ready

- [ ] Certificados TLS válidos
- [ ] .env production configurado
- [ ] Backups automáticos
- [ ] Monitoreo (Prometheus/Grafana)
- [ ] Logs centralizados (ELK, CloudWatch)
- [ ] CI/CD pipeline (GitHub Actions, GitLab CI)

---

### Tarea 11.2: Documentación

- [ ] README.md completo
- [ ] CONTRIBUTING.md
- [ ] Deploy guide
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Security policy

---

### Tarea 11.3: Deploy

```bash
# Build imágenes para producción
docker-compose -f docker-compose.prod.yml build

# Deploy a servidor
docker-compose -f docker-compose.prod.yml up -d

# Verificar salud
curl https://firma-digital.es/health
```

---

## CRONOGRAMA RESUMIDO

```
Semana 1-2:   Infraestructura (Docker, BD, .env)
Semana 3-4:   Auth (Certificados, JWT)
Semana 5-6:   Documentos (Upload, CRUD)
Semana 7-8:   Firma (Validación, TSA)
Semana 9:     Workflows y Auditoría
Semana 10:    Frontend base
Semana 11:    Frontend documentos
Semana 12:    Frontend firma
Semana 13:    Frontend workflows
Semana 14-15: Testing y QA
Semana 16:    Deploy y documentación
```

---

## DEPENDENCIAS ENTRE FASES

```
Fase 1 (Infraestructura)
    ↓
Fase 2 (Auth)
    ↓
Fase 3 (Documentos) + Fase 10 (Testing backend)
    ↓
Fase 4 (Firma) + Fase 5 (Workflows)
    ↓
Fase 6 (Frontend base)
    ↓
Fase 7 (Frontend docs) + Fase 11 (Testing frontend)
    ↓
Fase 8 (Frontend firma)
    ↓
Fase 9 (Frontend workflows)
    ↓
Fase 12 (Deploy)
```

---

## CHECKPOINTS DE VALIDACIÓN

### Después de Fase 2 (Auth)
```bash
✅ Usuario puede loguear con certificado
✅ JWT tokens funcionales
✅ Endpoints protegidos requieren autenticación
```

### Después de Fase 3 (Documentos)
```bash
✅ Usuarios pueden subir PDFs
✅ PDFs se almacenan en MongoDB
✅ Usuarios ven su lista de documentos
```

### Después de Fase 4 (Firma)
```bash
✅ Usuarios pueden firmar documentos
✅ Firma se valida criptográficamente
✅ TSA proporciona timestamp
✅ Auditoría registra cada operación
```

### Después de Fase 9 (Frontend)
```bash
✅ UI funcional para todos los flujos
✅ Certificado se solicita correctamente
✅ Integración frontend-backend correcta
```

### Antes de Despliegue (Fase 11)
```bash
✅ 80%+ test coverage
✅ Security audit pasado
✅ Performance acceptable
✅ Backups automáticos configurados
✅ Monitoreo en lugar
```

---

## REFERENCIAS RÁPIDAS

- ARCHITECTURE.md → Visión general
- DATABASE.md → Esquemas
- API_SPEC.md → Endpoints
- SECURITY.md → Checklist de seguridad
- DOCKER.md → Infraestructura
- FRONTEND_SPEC.md → UI/UX
- BACKEND_SPEC.md → Lógica de negocio
