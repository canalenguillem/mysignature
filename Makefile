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
