# DOCKER - COMPOSICIÓN DE SERVICIOS

## Resumen

Toda la aplicación se despliega con **Docker Compose**:
- Frontend (React + Vite)
- Backend (FastAPI)
- MariaDB
- MongoDB
- Redis
- Nginx (reverse proxy + HTTPS)

---

## 1. ESTRUCTURA DE CARPETAS

```
firma-digital-eidas/
├── docker-compose.yml         # Orquestación principal
├── docker-compose.prod.yml    # Producción (override)
├── .dockerignore
├── .env.example
├── .env                        # NO commitear a git
│
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
│
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
│
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── ssl/                   # Certificados TLS (NO en git)
│   │   ├── server.crt
│   │   ├── server.key
│   │   └── ca.crt
│   └── conf.d/
│       └── default.conf
│
└── docker-entrypoint.sh       # Script de inicialización
```

---

## 2. DOCKER-COMPOSE.YML (DESARROLLO)

```yaml
version: "3.9"

services:
  # ========== BASES DE DATOS ==========
  
  mariadb:
    image: mariadb:10.5
    container_name: firma_digital_mariadb
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_INITDB_SKIP_TZINFO: "yes"
    ports:
      - "3306:3306"
    volumes:
      - mariadb_data:/var/lib/mysql
      - ./backend/app/database/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10
    networks:
      - firma-network
    environment:
      TZ: "Europe/Madrid"
  
  mongodb:
    image: mongo:4.4
    container_name: firma_digital_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_DATABASE}
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./backend/scripts/mongo-init.js:/docker-entrypoint-initdb.d/init.js
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      timeout: 10s
      retries: 5
    networks:
      - firma-network
  
  redis:
    image: redis:6-alpine
    container_name: firma_digital_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 3s
      retries: 5
    networks:
      - firma-network
    command: redis-server --appendonly yes
  
  # ========== BACKEND ==========
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: firma_digital_backend
    environment:
      DEBUG: ${DEBUG}
      DATABASE_URL: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mariadb:3306/${DB_NAME}
      MONGODB_URL: mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017
      MONGODB_DATABASE: ${MONGO_DATABASE}
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      TSA_URL: ${TSA_URL}
      FNMT_ROOT_CA_PEM: /etc/certs/fnmt-root-ca.pem
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./certs/fnmt-root-ca.pem:/etc/certs/fnmt-root-ca.pem:ro
    depends_on:
      mariadb:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - firma-network
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      timeout: 10s
      retries: 5
  
  # ========== FRONTEND ==========
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: ${VITE_API_URL}
    container_name: firma_digital_frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    networks:
      - firma-network
    depends_on:
      - backend
    command: npm run dev
  
  # ========== NGINX REVERSE PROXY ==========
  
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: firma_digital_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    networks:
      - firma-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      timeout: 10s
      retries: 5

networks:
  firma-network:
    driver: bridge

volumes:
  mariadb_data:
    driver: local
  mongodb_data:
    driver: local
  redis_data:
    driver: local
```

---

## 3. DOCKER-COMPOSE.PROD.YML

```yaml
version: "3.9"

services:
  mariadb:
    image: mariadb:10.5
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped
    volumes:
      - mariadb_data:/var/lib/mysql
    networks:
      - firma-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10
  
  mongodb:
    image: mongo:4.4
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_DATABASE}
    restart: unless-stopped
    volumes:
      - mongodb_data:/data/db
      - mongodb_backup:/backup
    networks:
      - firma-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      timeout: 10s
      retries: 5
  
  redis:
    image: redis:6-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - firma-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 3s
      retries: 5
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      cache_from:
        - ${REGISTRY}/firma-digital-backend:latest
    image: ${REGISTRY}/firma-digital-backend:${VERSION}
    restart: unless-stopped
    environment:
      DEBUG: "false"
      DATABASE_URL: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mariadb:3306/${DB_NAME}
      MONGODB_URL: mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      JWT_SECRET: ${JWT_SECRET}
      TSA_URL: ${TSA_URL}
    networks:
      - firma-network
    depends_on:
      mariadb:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      timeout: 10s
      retries: 5
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        VITE_API_URL: ${VITE_API_URL}
      cache_from:
        - ${REGISTRY}/firma-digital-frontend:latest
    image: ${REGISTRY}/firma-digital-frontend:${VERSION}
    restart: unless-stopped
    networks:
      - firma-network
    depends_on:
      - backend
  
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    image: ${REGISTRY}/firma-digital-nginx:${VERSION}
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt/live/${DOMAIN}/fullchain.pem:/etc/nginx/certs/server.crt:ro
      - /etc/letsencrypt/live/${DOMAIN}/privkey.pem:/etc/nginx/certs/server.key:ro
      - ./certs/ca.crt:/etc/nginx/certs/ca.crt:ro
    networks:
      - firma-network
    depends_on:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      timeout: 10s
      retries: 5

networks:
  firma-network:
    driver: bridge

volumes:
  mariadb_data:
    driver: local
  mongodb_data:
    driver: local
  mongodb_backup:
    driver: local
  redis_data:
    driver: local
```

---

## 4. NGINX.CONF

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    # Load balancing (si hay múltiples backends)
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:5173;
    }

    # Redirigir HTTP a HTTPS
    server {
        listen 80;
        server_name _;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS con mTLS
    server {
        listen 443 ssl http2;
        server_name firma-digital.es www.firma-digital.es;

        # Certificados TLS (servidor)
        ssl_certificate /etc/nginx/certs/server.crt;
        ssl_certificate_key /etc/nginx/certs/server.key;

        # TLS Configuration
        ssl_protocols TLSv1.3 TLSv1.2;
        ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Autenticación mutua (mTLS) - Cliente presenta certificado
        ssl_client_certificate /etc/nginx/certs/ca.crt;
        ssl_verify_client optional;
        ssl_verify_depth 2;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

        # API Backend
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            # Pasar certificado cliente al backend
            proxy_set_header X-SSL-Client-Cert $ssl_client_cert;
            proxy_set_header X-SSL-Client-Verify $ssl_client_verify;
            proxy_set_header X-SSL-Client-Depth $ssl_client_s_dn;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 30s;
        }

        # Auth endpoints (rate limit más restrictivo)
        location /api/auth/ {
            limit_req zone=auth_limit burst=5 nodelay;
            
            proxy_set_header X-SSL-Client-Cert $ssl_client_cert;
            proxy_set_header X-SSL-Client-Verify $ssl_client_verify;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend (React development)
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "OK";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 5. ENV.EXAMPLE

```bash
# ========== APP ==========
DEBUG=true
APP_NAME=Firma Digital EIDAS

# ========== MARIADB ==========
DB_HOST=mariadb
DB_PORT=3306
DB_NAME=firma_digital
DB_USER=firma_user
DB_PASSWORD=change_me_secure_password
DB_ROOT_PASSWORD=change_me_root_password

# ========== MONGODB ==========
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_USER=firma_user
MONGO_PASSWORD=change_me_secure_password
MONGO_DATABASE=firma_digital

# ========== REDIS ==========
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change_me_secure_password

# ========== JWT ==========
JWT_SECRET=your_very_long_secret_key_change_this_in_production

# ========== TSA (Timestamp Authority) ==========
TSA_URL=http://tst.lacaixa.es

# ========== FRONTEND ==========
VITE_API_URL=https://api.firma-digital.es/v1
VITE_LOG_LEVEL=info

# ========== PRODUCTION ==========
DOMAIN=firma-digital.es
REGISTRY=your-docker-registry.io/firma-digital
VERSION=1.0.0
```

---

## 6. MAKEFILE

```makefile
.PHONY: help dev prod up down logs build test clean

help:
	@echo "Comandos disponibles:"
	@echo "  make dev           - Iniciar en modo desarrollo"
	@echo "  make prod          - Iniciar en modo producción"
	@echo "  make up            - Levantar servicios"
	@echo "  make down          - Detener servicios"
	@echo "  make build         - Construir imágenes"
	@echo "  make logs          - Ver logs"
	@echo "  make test          - Ejecutar tests"
	@echo "  make clean         - Limpiar datos"
	@echo "  make migrate       - Ejecutar migraciones"
	@echo "  make seed          - Sembrar datos de prueba"

dev:
	docker-compose up -d

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

rebuild:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-nginx:
	docker-compose logs -f nginx

test:
	docker-compose exec backend pytest tests/

test-backend:
	docker-compose exec backend pytest tests/test_certificates.py

test-coverage:
	docker-compose exec backend pytest --cov=app tests/

shell-backend:
	docker-compose exec backend bash

shell-mongodb:
	docker-compose exec mongodb mongosh

shell-mariadb:
	docker-compose exec mariadb mysql -u${DB_USER} -p${DB_PASSWORD} ${DB_NAME}

migrate:
	docker-compose exec backend alembic upgrade head

migrate-status:
	docker-compose exec backend alembic current

seed:
	docker-compose exec backend python scripts/seed_data.py

clean:
	docker-compose down -v
	rm -rf ./backend/app/database/migrations/versions/__pycache__

ps:
	docker-compose ps

stats:
	docker stats
```

---

## 7. DOCKERFILE BACKEND

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. DOCKERFILE FRONTEND

```dockerfile
# Development
FROM node:18-alpine as dev

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]

# Production Build
FROM node:18-alpine as build

WORKDIR /app

ARG VITE_API_URL

COPY package*.json .
RUN npm ci

COPY . .

ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production Serve
FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

---

## 9. DOCKERFILE NGINX

```dockerfile
FROM nginx:alpine

RUN apk add --no-cache curl

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

---

## 10. STARTUP CHECKLIST

```bash
# 1. Crear archivos de configuración
cp .env.example .env
# Editar .env con valores reales

# 2. Crear certificados autofirmados (desarrollo)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key \
    -out certs/server.crt -days 365 -nodes

# 3. Construir imágenes
make build

# 4. Levantar servicios
make dev

# 5. Verificar salud
make ps

# 6. Ver logs
make logs

# 7. Ejecutar migraciones
make migrate

# 8. Acceder a la aplicación
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Nginx: https://localhost (desarrollo, certificado autofirmado)
```

---

## 11. MONITOREO EN PRODUCCIÓN

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:8000']
  
  - job_name: 'mariadb'
    static_configs:
      - targets: ['localhost:3306']
```

---

## 12. BACKUP AUTOMÁTICO

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/firma-digital"
DATE=$(date +%Y%m%d_%H%M%S)

# MariaDB
docker-compose exec -T mariadb mysqldump --all-databases \
    > $BACKUP_DIR/mariadb_$DATE.sql

# MongoDB
docker-compose exec -T mongodb mongodump \
    --out $BACKUP_DIR/mongodb_$DATE/

# Encriptar
openssl enc -aes-256-cbc -salt \
    -in $BACKUP_DIR/mariadb_$DATE.sql \
    -out $BACKUP_DIR/mariadb_$DATE.sql.enc

# Enviar a S3
aws s3 sync $BACKUP_DIR s3://backup-bucket/firma-digital/

# Limpiar local (opcional)
find $BACKUP_DIR -mtime +7 -delete
```

---

## Referencias

- Docker Compose: https://docs.docker.com/compose/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Nginx Documentation: https://nginx.org/en/docs/
