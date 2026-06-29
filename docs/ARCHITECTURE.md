# ARQUITECTURA - PLATAFORMA DE FIRMA DIGITAL EIDAS

## Visión General

Plataforma web para firma digital de PDFs con certificados digitales españoles (FNMT), cumpliendo normativa EIDAS (Reglamento 910/2014). Soporta flujos individuales (usuario firma su documento) y colaborativos (múltiples usuarios firman el mismo documento).

## Stack Tecnológico

```
Frontend:
  - React 18+ con TypeScript
  - Vite como bundler
  - Web Crypto API para operaciones criptográficas
  - pdf-lib para manipulación de PDFs
  - Axios para API calls

Backend:
  - FastAPI (Python 3.10+)
  - SQLAlchemy ORM
  - PyMongo para MongoDB
  - Redis client
  - python-jose para JWT
  - pyca/cryptography para validación de certificados

Bases de Datos:
  - MariaDB 10.5+ (datos estructurados, auditoría)
  - MongoDB 4.4+ (almacenamiento de PDFs)
  - Redis 6+ (sesiones, cache)

Orquestación:
  - Docker & Docker Compose
  - Nginx reverse proxy
  - HTTPS/TLS obligatorio
```

## Estructura del Proyecto

```
firma-digital-eidas/
├── docker-compose.yml              # Orquestación de todos los servicios
├── .env.example                    # Variables de entorno plantilla
├── .gitignore
├── README.md
│
├── backend/                        # API FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                # Entrada, middlewares, lifespan
│   │   ├── config.py              # Configuración (env vars)
│   │   │
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── certificates.py    # Validación de cert X.509, cadenas
│   │   │   ├── signature_validation.py  # Validar firmas en PDFs
│   │   │   ├── tsa_client.py      # Cliente RFC 3161 para Timestamp
│   │   │   └── jwt_handler.py     # JWT tokens para sesiones
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # SQLAlchemy User model
│   │   │   ├── document.py        # Document model (metadatos)
│   │   │   ├── signature.py       # Signature log
│   │   │   ├── audit_log.py       # Auditoría completa
│   │   │   └── workflow.py        # Flujo colaborativo
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # POST /auth/validate-cert
│   │   │   ├── documents.py       # CRUD de documentos
│   │   │   └── signatures.py      # POST /sign, GET /audit
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── certificate_service.py   # Lógica de validación
│   │   │   ├── document_service.py      # Gestión documentos
│   │   │   ├── signature_service.py     # Orquestación de firma
│   │   │   ├── audit_service.py        # Log de auditoría
│   │   │   ├── pdf_processor.py        # Validación PDF + embedding
│   │   │   └── tsa_service.py          # Timestamp requests
│   │   │
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py      # Conexiones a MariaDB, MongoDB
│   │   │   ├── session.py         # SessionLocal factory
│   │   │   └── migrations/        # Alembic migrations
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Pydantic models para request/response
│   │   │   ├── document.py
│   │   │   └── signature.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py          # Logging centralizado
│   │       └── errors.py          # Excepciones custom
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_certificates.py
│       ├── test_signature_validation.py
│       └── test_tsa_integration.py
│
├── frontend/                       # React + Vite
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── Auth/
│   │   │   │   ├── CertificateValidator.tsx    # Solicitar cert del navegador
│   │   │   │   ├── AuthGuard.tsx               # Proteger rutas
│   │   │   │   └── SessionStatus.tsx
│   │   │   │
│   │   │   ├── DocumentUpload/
│   │   │   │   ├── PDFUploader.tsx             # Input file PDF
│   │   │   │   └── DocumentPreview.tsx
│   │   │   │
│   │   │   ├── SignaturePanel/
│   │   │   │   ├── SignatureForm.tsx           # UI para firmar
│   │   │   │   ├── SignatureProgress.tsx       # Estados de firma
│   │   │   │   └── SignatureVerification.tsx   # Validar antes de firmar
│   │   │   │
│   │   │   ├── WorkflowPanel/
│   │   │   │   ├── WorkflowViewer.tsx          # Ver flujo colaborativo
│   │   │   │   ├── PendingSignatures.tsx       # Pendientes del usuario
│   │   │   │   └── SignatureHistory.tsx
│   │   │   │
│   │   │   ├── AuditLog/
│   │   │   │   ├── AuditViewer.tsx             # Historial completo
│   │   │   │   └── CertificateDetails.tsx
│   │   │   │
│   │   │   └── Common/
│   │   │       ├── Layout.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   │
│   │   ├── services/
│   │   │   ├── cryptoService.ts        # Web Crypto API wrappers
│   │   │   ├── certificateService.ts   # Validación certs en cliente
│   │   │   ├── apiService.ts           # Axios + interceptors
│   │   │   ├── pdfService.ts           # pdf-lib utilities
│   │   │   └── storageService.ts       # LocalStorage/SessionStorage
│   │   │
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   ├── certificate.ts
│   │   │   ├── document.ts
│   │   │   ├── signature.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useCertificate.ts
│   │   │   ├── useDocument.ts
│   │   │   └── useSignature.ts
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── DocumentDetailPage.tsx
│   │   │   └── AuditPage.tsx
│   │   │
│   │   ├── styles/
│   │   │   └── global.css
│   │   │
│   │   └── utils/
│   │       ├── formatters.ts
│   │       └── validators.ts
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   └── tests/
│       ├── certificateService.test.ts
│       └── cryptoService.test.ts
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf                  # Configuración reverse proxy + HTTPS
│
└── docs/
    ├── ARCHITECTURE.md             # Este archivo
    ├── SECURITY.md
    ├── DATABASE.md
    ├── API_SPEC.md
    ├── FRONTEND_SPEC.md
    ├── BACKEND_SPEC.md
    ├── DOCKER.md
    └── IMPLEMENTATION_ORDER.md
```

## Flujos Principales

### Flujo 1: Autenticación con Certificado Digital

```
1. Usuario accede a https://app.example.com
2. Frontend → RequestClientCertificate (TLS)
3. Navegador solicita certificado (igual que Agencia Tributaria)
4. Usuario selecciona su certificado FNMT
5. Frontend → Extrae datos del certificado (subject, issuer, serialNumber)
6. Frontend → Valida certificado localmente
   - Validar formato X.509
   - Validar fechas (not-before, not-after)
   - Validar extensiones críticas (Digital Signature)
7. Frontend → POST /api/auth/validate-cert { certData, certificatePEM }
8. Backend → Valida cadena de certificados contra FNMT root
9. Backend → Verifica contra lista negra (CRL/OCSP)
10. Backend → Crea sesión JWT
11. Backend → Retorna token + user info
12. Frontend → Almacena token en sessionStorage
13. Usuario autenticado ✓
```

### Flujo 2: Firma Individual (Usuario firma su PDF)

```
1. Usuario descarga o sube PDF
2. Frontend → Leer PDF con pdf-lib
3. Frontend → Validar estructura PDF
4. Frontend → Mostrar preview + metadatos
5. Usuario click "Firmar Documento"
6. Frontend → Calcular hash del PDF (SHA-256)
7. Frontend → Web Crypto API firma el hash
   - SubtleCrypto.sign() usa el certificado del navegador
   - Retorna firma digital (Array buffer)
8. Frontend → Convertir firma a base64
9. Frontend → POST /api/documents/{id}/sign
   {
     document_id: "...",
     signature_base64: "...",
     hash_algorithm: "SHA-256",
     signature_algorithm: "RSA-PSS",
     certificate_pem: "-----BEGIN CERTIFICATE-----..."
   }
10. Backend → Recibe firma + certificado
11. Backend → Valida la firma criptográficamente
    - Extrae clave pública del certificado
    - Verifica que firma(hash) == certPublicKey
12. Backend → Si válida, solicita timestamp a TSA
    - RFC 3161 request
    - TSA retorna TimeStampToken
13. Backend → Embebe timestamp en PDF
    - Añade diccionario de firma PDF
    - Incluye timestamp como evidencia
14. Backend → Guarda PDF firmado en MongoDB
15. Backend → Crea registros en auditoría (MariaDB)
    - signatures table
    - audit_logs table
16. Backend → Retorna confirmación al frontend
17. Frontend → Muestra "✓ Documento firmado"
```

### Flujo 3: Firma Colaborativa (Múltiples usuarios) - OPCIÓN HÍBRIDA

```
1. Usuario A sube documento
   ↓
2. Usuario A click "Asignar Firmas"
   ↓
3. Frontend muestra formulario de búsqueda
   - Input: buscar por email/nombre
   - Ej: "maria" o "maria@empresa.es"
   ↓
4. Backend busca en tabla users:
   - Usuarios con email coincidente
   - Usuarios con nombre coincidente
   - Solo si tienen certificado vigente
   - Filtra por organización (opcional)
   ↓
5. Frontend muestra resultados:
   - María García (maria@empresa.es) - Org: Empresa S.L. ✓ Cert válido
   - Carlos López (carlos@empresa.es) - Org: Empresa S.L. ✓ Cert válido
   ↓
6. Usuario A selecciona María + Carlos
   ↓
7. Usuario A elige tipo de firma:
   - Radio button: Paralela (todos a la vez)
   - Radio button: Secuencial (uno tras otro)
   ↓
8. Usuario A click "Crear Workflow"
   ↓
9. Backend valida:
   - Ambos usuarios existen
   - Ambos tienen certs vigentes
   - Ambos pertenecen a organización correcta
   ↓
10. Backend crea:
    - Registro en signature_workflows (status: pending)
    - 2 registros en workflow_assignments (status: pending)
    - Si secuencial: define sequence_number
    - Actualiza documents.status = "pending_signatures"
    ↓
11. María y Carlos ven documento en dashboard:
    - "Pendientes de mi firma" → Documento A
    - Otros firmantes requeridos
    - Tipo: Paralela o Secuencial
    ↓
12. María abre documento y firma
    ↓
13. Backend registra firma de María:
    - Crea registro en signatures
    - Actualiza workflow_assignments (María: signed)
    - Si secuencial: desbloquea a Carlos
    - Si paralela: sigue esperando a Carlos
    ↓
14. Carlos recibe notificación (si paralela) o le aparece disponible (si secuencial)
    ↓
15. Carlos firma
    ↓
16. Backend detecta que todas las firmas están:
    - Actualiza documents.status = "fully_signed"
    - Cierra workflow
    - Documento listo ✓
```

**Características de esta estrategia (OPCIÓN 3 - HÍBRIDA):**
- **Búsqueda flexible**: Por email o nombre (case-insensitive)
- **Validación de certificado**: Al momento de crear workflow
- **Tipos de firma**: Usuario elige paralela o secuencial
- **Requisito previo**: Usuarios deben haberse autenticado al menos una vez
- **Filtro opcional**: Por organización del usuario
- **Notificaciones**: Automáticas cuando hay cambios de estado
- **Seguridad**: Solo usuarios con certificados vigentes pueden ser asignados

### Flujo 4: Validación y Auditoría

```
1. Usuario accede a documento já firmado
2. Frontend → GET /api/documents/{id}
3. Backend → Retorna metadata + historial de firmas
4. Frontend → GET /api/documents/{id}/audit
5. Backend → Retorna audit log completo
   - Quién firmó
   - Cuándo
   - Con qué certificado (fingerprint)
   - Timestamp TSA
   - Estado de validación
6. Frontend → Muestra en tabla/timeline
7. Usuario puede descargar PDF firmado
8. Usuario puede verificar firmas con software externo
```

## Principios de Seguridad

### Autenticación
- TLS mutuo (cliente presenta certificado)
- JWT tokens con expiración (15 min access, 7 días refresh)
- Invalidación de sesión en logout

### Criptografía
- SHA-256 para hashing
- RSA-PSS para firma digital (mínimo RSA-2048)
- HTTPS/TLS 1.3 obligatorio
- No almacenar claves privadas del usuario

### Auditoría
- Log inmutable de cada operación criptográfica
- Timestamp de TSA como prueba de no-repudio
- MariaDB como registro permanente
- No permitir eliminación de audit logs

### Validación
- Validar certificados contra FNMT root
- Revisar listas negras (CRL/OCSP)
- Validar estructura de PDFs
- Validar firmas antes de aceptarlas

## Integraciones Externas

### 1. Timestamp Authority (TSA)
- Protocolo RFC 3161
- Proveedores en España:
  - CaixaBank (http://tst.lacaixa.es)
  - Otros proveedores EIDAS cualificados
- Cada firma incluye timestamp → no-repudio

### 2. Autoridades Certificantes (AC)
- FNMT (Fábrica Nacional de Moneda y Timbre)
- Validar certificados contra raíz FNMT
- Revisar revocación (CRL/OCSP)

## Componentes Críticos

| Componente | Ubicación | Responsabilidad | Criticidad |
|---|---|---|---|
| CertificateValidator | Frontend | Validar X.509 inicial | CRÍTICA |
| WebCryptoSigner | Frontend | Firmar con cert navegador | CRÍTICA |
| PDFSignatureValidator | Backend | Validar firma en PDF | CRÍTICA |
| TSAClient | Backend | RFC 3161 con timestamp | CRÍTICA |
| AuditLogger | Backend | Log inmutable | CRÍTICA |
| DocumentManager | Backend | CRUD seguro | ALTA |
| JWTHandler | Backend | Sesiones | ALTA |

## Consideraciones EIDAS

- ✅ Firma Avanzada (Art. 26 EIDAS)
  - Vinculada únicamente al firmante
  - Basada en certificado cualificado
  - Creada mediante SSCD (Dispositivo Seguro)
  
- ✅ Timestamp (Art. 41 EIDAS)
  - TSA cualificada
  - Vinculada a la firma
  - Prueba de integridad + momento
  
- ✅ Cadena de Certificados
  - Raíz verificable (FNMT)
  - Validación CRL/OCSP
  
- ✅ Auditoría
  - Trazabilidad completa
  - Datos no repudiables

## Selección de Usuarios para Firma Colaborativa

### Estrategia Elegida: OPCIÓN 3 (HÍBRIDA)

**Flujo de Selección (10 pasos):**

```
1. Usuario A sube documento
2. Click "Asignar Firmas"
3. Búsqueda rápida por email/nombre (ej: "maria@empresa.es")
4. Sistema filtra:
   - Usuarios con emails válidos
   - Certificados vigentes
   - Organización (opcional)
5. Selecciona María García + Carlos López
6. Define si es paralela o secuencial
7. Crea workflow
8. María y Carlos ven documento en "Pendientes"
9. Cada uno firma con su certificado
10. Documento se cierra cuando todas las firmas están
```

### Características de Esta Estrategia

**Búsqueda:**
- Por email o nombre (case-insensitive)
- Solo usuarios que ya se autenticaron (tienen certificado en BD)
- Respuesta incluye estado del certificado (válido/expirado)

**Validación:**
- Al crear workflow se validan todos los certificados
- Si certificado expira después, se detecta al intentar firmar
- Rate limiting: 50 req/min por usuario

**Tipos de Firma:**
- **Paralela**: Todos firman cuando quieran, sin orden
- **Secuencial**: Orden definido, siguiente solo cuando anterior termina

**Seguridad:**
- Solo usuarios con certs vigentes en búsqueda
- Validación en creación de workflow
- Si cert expira → error 401 al intentar firmar

### Endpoints Necesarios

**Backend:**
- `GET /users/search?query=...` → búsqueda de usuarios
- `GET /users/by-organization/{org}` → usuarios por organización
- `POST /documents/{id}/workflow` → crear workflow con asignación
- `GET /documents/{id}/workflow` → estado del workflow

**Frontend:**
- Input de búsqueda que llama a `/users/search`
- Formulario para asignar signers y tipo de firma
- Vista de "Documentos pendientes de mi firma"
- Timeline que muestra quién firmó y en qué orden

---

## Próximos Pasos

Ver `IMPLEMENTATION_ORDER.md` para orden de construcción recomendado.
