# mysignature — Plataforma de Firma Digital eIDAS

Plataforma web para **firmar PDFs con certificados digitales españoles (FNMT)** y
verificar firmas, conforme al **Reglamento (UE) 910/2014 (eIDAS)**. Soporta firma
individual y colaborativa (paralela o secuencial), sellado de tiempo cualificado
(TSA, RFC 3161) y auditoría inmutable.

> Estado: **backend funcional (Fases 1–4)**. Frontend y workflows colaborativos en
> construcción. Ver [Hoja de ruta](#hoja-de-ruta).

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Stack](#stack)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Puesta en marcha (Docker)](#puesta-en-marcha-docker)
- [Variables de entorno](#variables-de-entorno)
- [API](#api)
- [Flujo de firma](#flujo-de-firma)
- [Hoja de ruta](#hoja-de-ruta)
- [Documentación](#documentación)

---

## Arquitectura

```
┌─────────┐   HTTPS/mTLS   ┌─────────┐   REST   ┌──────────────┐
│ Frontend│ ─────────────► │  Nginx  │ ───────► │   Backend    │
│ (React) │                │ (proxy) │          │  (FastAPI)   │
└─────────┘                └─────────┘          └──────┬───────┘
                                                        │
                        ┌───────────────┬───────────────┼───────────────┐
                        ▼               ▼               ▼               ▼
                   ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
                   │ MariaDB │    │ MongoDB  │    │  Redis  │    │   TSA    │
                   │ (datos, │    │  (PDFs   │    │(sesiones│    │ RFC 3161 │
                   │ auditor.)│   │ binarios)│    │, cache) │    │ (externa)│
                   └─────────┘    └──────────┘    └─────────┘    └──────────┘
```

- **MariaDB** — usuarios, metadatos de documentos, firmas, workflows y auditoría
  (`audit_logs` es inmutable vía triggers).
- **MongoDB** — binarios de los PDFs (original/firmado) y metadata de firma.
- **Redis** — refresh tokens y rate limiting.
- La clave privada del usuario **nunca** sale del navegador: la firma se realiza en
  el cliente y el backend la **verifica** criptográficamente.

Detalle completo en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Stack

| Capa        | Tecnología                                              |
|-------------|---------------------------------------------------------|
| Backend     | FastAPI · SQLAlchemy 2 · PyMongo · redis-py             |
| Cripto      | `pyca/cryptography` · `asn1crypto` (TSA) · `python-jose` (JWT) |
| PDF         | `pypdf`                                                 |
| Bases datos | MariaDB 10.5 · MongoDB 4.4 · Redis 6                    |
| Frontend    | React 18 · Vite · TypeScript *(en construcción)*        |
| Infra       | Docker Compose · Nginx (reverse proxy + mTLS)           |

---

## Estructura del proyecto

```
mysignature/
├── docker-compose.yml          # Orquestación (dev)
├── docker-compose.prod.yml     # Override de producción
├── Makefile                    # Atajos (make dev / build / logs / migrate…)
├── .env.example                # Plantilla de variables de entorno
│
├── backend/                    # API FastAPI
│   └── app/
│       ├── main.py             # Entrada ASGI, middlewares, routers
│       ├── config.py           # Settings (env)
│       ├── database/           # Conexiones MariaDB/Mongo/Redis · init.sql
│       ├── models/             # SQLAlchemy (User, Document, Signature, …)
│       ├── schemas/            # Pydantic (request/response)
│       ├── security/           # certificates · signature_validation · tsa_client · jwt
│       ├── services/           # document · signature · certificate · audit
│       ├── routes/             # auth · documents · signatures
│       └── middleware/         # security headers · rate-limit
│
├── frontend/                   # React + Vite (en construcción)
├── nginx/                      # Reverse proxy + TLS/mTLS
└── docs/                       # Especificaciones completas
```

---

## Puesta en marcha (Docker)

Requisitos: **Docker** y **Docker Compose**.

```bash
# 1. Configuración
cp .env.example .env            # edita los valores si quieres

# 2. Levantar bases de datos + backend
docker compose up -d --build mariadb mongodb redis backend

# 3. Comprobar salud
curl http://localhost:8000/health      # -> {"status":"ok"}
```

- **API:** http://localhost:8000
- **Swagger UI (interactivo):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

> El frontend y nginx todavía no se levantan (frontend sin scaffold aún; es la
> Fase 6). De momento se trabaja contra el backend directamente.

### Puertos ocupados en tu máquina

Si ya tienes servicios en 3306/6379/8000, crea un `docker-compose.override.yml`
(ignorado por git) remapeando solo los puertos de **host**:

```yaml
services:
  mariadb:  { ports: !override ["13306:3306"] }
  redis:    { ports: !override ["16379:6379"] }
  backend:  { ports: !override ["18080:8000"] }
  mongodb:
    ports: !override ["27018:27017"]
    # mongo:4.4 trae el shell legacy `mongo`, no `mongosh`
    healthcheck:
      test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
```

Con ese override, la API queda en `http://localhost:18080`.

### Comandos útiles (Makefile)

```bash
make dev        # levantar servicios
make logs       # seguir logs
make down       # parar
make ps         # estado
```

---

## Variables de entorno

Definidas en [.env.example](.env.example). Las principales:

| Variable        | Descripción                                  |
|-----------------|----------------------------------------------|
| `DB_*`          | Credenciales/host de MariaDB                 |
| `MONGO_*`       | Credenciales/host de MongoDB                 |
| `REDIS_*`       | Conexión a Redis                             |
| `JWT_SECRET`    | Secreto de firma de los JWT                  |
| `TSA_URL`       | Autoridad de sellado de tiempo (RFC 3161)    |
| `VITE_API_URL`  | URL de la API para el frontend               |

---

## API

Base: `/api/v1`. Documentación viva en `/docs`. Contratos completos en
[docs/API_SPEC.md](docs/API_SPEC.md).

### Autenticación
| Método | Ruta                       | Descripción                          |
|--------|----------------------------|--------------------------------------|
| POST   | `/auth/validate-cert`      | Valida certificado FNMT y emite JWT  |
| POST   | `/auth/refresh`            | Renueva el access token              |
| POST   | `/auth/logout`             | Revoca el refresh token              |
| GET    | `/auth/me`                 | Usuario autenticado                  |

### Documentos
| Método | Ruta                          | Descripción                     |
|--------|-------------------------------|---------------------------------|
| POST   | `/documents`                  | Subir PDF (multipart)           |
| GET    | `/documents`                  | Listar (filtros + paginación)   |
| GET    | `/documents/{id}`             | Detalle                         |
| GET    | `/documents/{id}/download`    | Descargar (original/firmado)    |
| DELETE | `/documents/{id}`             | Borrado lógico                  |

### Firmas
| Método | Ruta                                              | Descripción                |
|--------|---------------------------------------------------|----------------------------|
| POST   | `/documents/{id}/sign`                            | Firmar (verifica + sella)  |
| GET    | `/documents/{id}/signatures`                      | Historial de firmas        |
| POST   | `/documents/{id}/signatures/{sig_id}/verify`      | Verificar una firma        |

Todos los endpoints (salvo `/auth/validate-cert`) requieren
`Authorization: Bearer <JWT>`.

---

## Flujo de firma

1. El usuario se autentica con su **certificado FNMT** (mTLS / selección en el
   navegador) → backend valida X.509 y emite **JWT**.
2. Sube un PDF; el binario va a **MongoDB** y los metadatos a **MariaDB**.
3. El navegador calcula el **hash SHA-256** y firma con la clave privada del
   certificado (Web Crypto API).
4. El backend **verifica** la firma (RSA-PSS/ECDSA), solicita un **sello de tiempo
   TSA** (RFC 3161) y registra todo en **auditoría**.
5. El documento queda firmado; la auditoría es **inmutable** (no-repudio eIDAS).

---

## Hoja de ruta

Construcción por fases (ver [docs/IMPLEMENTATION_ORDER.md](docs/IMPLEMENTATION_ORDER.md)):

- [x] **Fase 1** — Infraestructura (Docker, BD, nginx, init scripts)
- [x] **Fase 2** — Autenticación (X.509 FNMT, JWT, rate-limit)
- [x] **Fase 3** — Gestión de documentos (CRUD + MongoDB)
- [x] **Fase 4** — Firma digital (verificación, TSA RFC 3161, auditoría)
- [ ] **Fase 5** — Workflows colaborativos + búsqueda de usuarios + rutas de auditoría
- [ ] **Fase 6-9** — Frontend (React): login, dashboard, panel de firma, workflows
- [ ] **Fase 10** — Testing y QA
- [ ] **Fase 11** — Despliegue de producción

### Pendientes técnicos conocidos
- Embebido **PAdES** real en el binario del PDF (hoy se guarda la metadata de firma
  y `signed_pdf` referencia el original).
- Validación de **revocación** de certificados (OCSP/CRL).
- Migraciones **Alembic** para producción (en dev el esquema lo crea `init.sql`).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)         | Visión general y flujos        |
| [API_SPEC.md](docs/API_SPEC.md)                 | Endpoints REST                 |
| [BACKEND_SPEC.md](docs/BACKEND_SPEC.md)         | Lógica de negocio backend      |
| [FRONTEND_SPEC.md](docs/FRONTEND_SPEC.md)       | Especificación de UI           |
| [DATABASE.md](docs/DATABASE.md)                 | Esquemas de datos              |
| [DOCKER.md](docs/DOCKER.md)                     | Infraestructura                |
| [SECURITY.md](docs/SECURITY.md)                 | Checklist de seguridad         |
| [IMPLEMENTATION_ORDER.md](docs/IMPLEMENTATION_ORDER.md) | Orden de construcción   |

---

## Licencia

Proyecto privado. Todos los derechos reservados.
