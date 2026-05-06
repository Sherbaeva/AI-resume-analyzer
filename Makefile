.PHONY: help dev prod down logs migrate shell test build-prod

# ─── Help ────────────────────────────────────────────────────
help:
	@echo ""
	@echo "ATS — Resume Analyzer & Matching System"
	@echo "─────────────────────────────────────────"
	@echo "  make dev          Start development environment"
	@echo "  make prod         Start production environment"
	@echo "  make down         Stop all containers"
	@echo "  make logs         Tail API logs"
	@echo "  make migrate      Run database migrations"
	@echo "  make shell        Open shell inside api container"
	@echo "  make test         Run tests locally"
	@echo "  make build-prod   Build production Docker image"
	@echo ""

# ─── Development ─────────────────────────────────────────────
dev:
	docker-compose up --build -d
	@echo "✓ Dev environment started"
	@echo "  API:     http://localhost:8000"
	@echo "  Swagger: http://localhost:8000/docs"
	@echo "  n8n:     http://localhost:5678"

# ─── Production ──────────────────────────────────────────────
prod: check-env-prod
	docker-compose -f docker-compose.prod.yml up --build -d
	@echo "✓ Production environment started"

check-env-prod:
	@test -f .env.prod || (echo "ERROR: .env.prod not found. Copy .env.prod.example and fill in values." && exit 1)

build-prod:
	docker build -f Dockerfile.prod -t ats-api:latest .
	@echo "✓ Production image built: ats-api:latest"

# ─── Common ──────────────────────────────────────────────────
down:
	docker-compose down

down-prod:
	docker-compose -f docker-compose.prod.yml down

logs:
	docker-compose logs -f api

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f api

migrate:
	docker-compose exec api alembic upgrade head

migrate-prod:
	docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

shell:
	docker-compose exec api bash

shell-prod:
	docker-compose -f docker-compose.prod.yml exec api bash

# ─── Tests ───────────────────────────────────────────────────
test:
	pytest -v

test-ci:
	pytest -v --tb=short --no-header -q
