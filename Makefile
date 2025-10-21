# Koroh Platform Docker Management

.PHONY: help build up down restart logs clean dev prod

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Default target
help:
	@echo "$(BLUE)Koroh Platform Docker Commands:$(NC)"
	@echo ""
	@echo "$(GREEN)Environment Management:$(NC)"
	@echo "  build         - Build all Docker images"
	@echo "  up            - Start all services in development mode"
	@echo "  down          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  logs          - Show logs for all services"
	@echo "  clean         - Remove all containers, volumes, and images"
	@echo "  dev           - Start development environment"
	@echo "  frontend-only - Start frontend-only environment (no backend required)"
	@echo "  prod          - Start production environment"
	@echo ""
	@echo "$(GREEN)Database Commands:$(NC)"
	@echo "  db-shell      - Open PostgreSQL shell"
	@echo "  db-migrate    - Run Django database migrations"
	@echo "  db-reset      - Reset database (WARNING: destroys all data)"
	@echo "  db-backup     - Create database backup"
	@echo "  db-restore    - Restore database from backup"
	@echo "  db-logs       - Show database logs"
	@echo ""
	@echo "$(GREEN)Frontend (Web) Commands:$(NC)"
	@echo "  web-shell     - Open shell in web container"
	@echo "  web-install   - Install npm dependencies"
	@echo "  web-build     - Build Next.js application"
	@echo "  web-test      - Run frontend tests"
	@echo "  web-lint      - Run frontend linting"
	@echo "  web-logs      - Show web container logs"
	@echo ""
	@echo "$(GREEN)Backend (API) Commands:$(NC)"
	@echo "  api-shell     - Open Django shell"
	@echo "  api-bash      - Open bash shell in API container"
	@echo "  api-migrate   - Run Django migrations"
	@echo "  api-test      - Run backend tests"
	@echo "  api-logs      - Show API container logs"
	@echo "  api-superuser - Create Django superuser"
	@echo "  api-static    - Collect static files"
	@echo ""
	@echo "$(GREEN)Celery Commands:$(NC)"
	@echo "  celery-logs   - Show Celery worker logs"
	@echo "  celery-status - Check Celery worker status"
	@echo "  celery-purge  - Purge all Celery tasks"
	@echo "  flower        - Open Celery Flower monitoring"
	@echo ""
	@echo "$(GREEN)Monitoring Commands:$(NC)"
	@echo "  monitor       - Open all monitoring dashboards"
	@echo "  prometheus    - Open Prometheus"
	@echo "  grafana       - Open Grafana"
	@echo "  mailhog       - Open MailHog"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@echo "  status        - Show status of all services"
	@echo "  ps            - Show running containers"
	@echo "  exec          - Execute command in container (usage: make exec SERVICE=web COMMAND='npm install')"

# Build all images
build:
	@echo "$(YELLOW)Building all Docker images...$(NC)"
	docker compose build

# Start development environment
dev: up

# Start all services
up:
	@echo "$(YELLOW)Starting all services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Services started successfully!$(NC)"
	@echo ""
	@echo "$(BLUE)Access URLs:$(NC)"
	@echo "  Frontend:    http://localhost:3000"
	@echo "  API:         http://localhost:8000"
	@echo "  PgAdmin:     http://localhost:5050"
	@echo "  MailHog:     http://localhost:8025"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3001"
	@echo "  Flower:      http://localhost:5555"

# Stop all services
down:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker compose down

# Restart all services
restart:
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker compose restart

# Show logs
logs:
	docker compose logs -f

# Start frontend-only environment
frontend-only:
	@echo "$(YELLOW)Starting frontend-only environment...$(NC)"
	docker compose -f docker-compose.frontend-only.yml up -d
	@echo "$(GREEN)Frontend started successfully!$(NC)"
	@echo ""
	@echo "$(BLUE)Access URL:$(NC)"
	@echo "  Frontend:    http://localhost:3000"
	@echo "  Demo Page:   http://localhost:3000/demo"
	@echo ""
	@echo "$(YELLOW)Note: Running in frontend-only mode with mock API$(NC)"

# Start production environment
prod:
	@echo "$(YELLOW)Starting production environment...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Clean up everything
clean:
	@echo "$(RED)WARNING: This will remove all containers, volumes, and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v --rmi all --remove-orphans; \
		docker system prune -f; \
		echo "$(GREEN)Cleanup completed!$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled.$(NC)"; \
	fi

# Database Commands
db-shell:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker compose exec postgres psql -U $${POSTGRES_USER:-koroh_user} -d $${POSTGRES_DB:-koroh_db}

db-migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker compose exec api python manage.py migrate

db-reset:
	@echo "$(RED)WARNING: This will destroy all database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down postgres; \
		docker volume rm koroh_postgres_data 2>/dev/null || true; \
		docker compose up -d postgres; \
		sleep 5; \
		docker compose exec api python manage.py migrate; \
		echo "$(GREEN)Database reset completed!$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled.$(NC)"; \
	fi

db-backup:
	@echo "$(BLUE)Creating database backup...$(NC)"
	mkdir -p backups
	docker compose exec postgres pg_dump -U $${POSTGRES_USER:-koroh_user} -d $${POSTGRES_DB:-koroh_db} > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created in backups/ directory$(NC)"

db-restore:
	@echo "$(BLUE)Available backups:$(NC)"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " backup_file; \
	if [ -f "backups/$$backup_file" ]; then \
		docker compose exec -T postgres psql -U $${POSTGRES_USER:-koroh_user} -d $${POSTGRES_DB:-koroh_db} < backups/$$backup_file; \
		echo "$(GREEN)Database restored from $$backup_file$(NC)"; \
	else \
		echo "$(RED)Backup file not found!$(NC)"; \
	fi

db-logs:
	docker compose logs -f postgres

# Frontend Commands
web-shell:
	@echo "$(BLUE)Opening shell in web container...$(NC)"
	docker compose exec web sh

web-install:
	@echo "$(BLUE)Installing npm dependencies...$(NC)"
	docker compose exec web npm install

web-build:
	@echo "$(BLUE)Building Next.js application...$(NC)"
	docker compose exec web npm run build

web-test:
	@echo "$(BLUE)Running frontend tests...$(NC)"
	docker compose exec web npm test

web-lint:
	@echo "$(BLUE)Running frontend linting...$(NC)"
	docker compose exec web npm run lint

web-logs:
	docker compose logs -f web

# Backend Commands
api-shell:
	@echo "$(BLUE)Opening Django shell...$(NC)"
	docker compose exec api python manage.py shell

api-bash:
	@echo "$(BLUE)Opening bash shell in API container...$(NC)"
	docker compose exec api bash

api-migrate:
	@echo "$(BLUE)Running Django migrations...$(NC)"
	docker compose exec api python manage.py migrate

api-test:
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker compose exec api python manage.py test

api-logs:
	docker compose logs -f api

api-superuser:
	@echo "$(BLUE)Creating Django superuser...$(NC)"
	docker compose exec api python manage.py createsuperuser

api-static:
	@echo "$(BLUE)Collecting static files...$(NC)"
	docker compose exec api python manage.py collectstatic --noinput

# Celery Commands
celery-logs:
	docker compose logs -f celery_worker celery_beat

celery-status:
	@echo "$(BLUE)Checking Celery worker status...$(NC)"
	docker compose exec celery_worker celery -A koroh_platform inspect active

celery-purge:
	@echo "$(YELLOW)Purging all Celery tasks...$(NC)"
	docker compose exec celery_worker celery -A koroh_platform purge -f

flower:
	@echo "$(BLUE)Opening Celery Flower...$(NC)"
	@echo "Flower is available at: http://localhost:5555"
	@command -v open >/dev/null 2>&1 && open http://localhost:5555 || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:5555 || \
	echo "Please open http://localhost:5555 in your browser"

# Monitoring Commands
monitor:
	@echo "$(BLUE)Opening monitoring dashboards...$(NC)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001"
	@echo "MailHog:    http://localhost:8025"
	@echo "Flower:     http://localhost:5555"

prometheus:
	@echo "$(BLUE)Opening Prometheus...$(NC)"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:9090 || \
	echo "Please open http://localhost:9090 in your browser"

grafana:
	@echo "$(BLUE)Opening Grafana...$(NC)"
	@command -v open >/dev/null 2>&1 && open http://localhost:3001 || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:3001 || \
	echo "Please open http://localhost:3001 in your browser"

mailhog:
	@echo "$(BLUE)Opening MailHog...$(NC)"
	@command -v open >/dev/null 2>&1 && open http://localhost:8025 || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8025 || \
	echo "Please open http://localhost:8025 in your browser"

# Utility Commands
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@docker compose ps

ps:
	@echo "$(BLUE)Running Containers:$(NC)"
	@docker compose ps

exec:
	@if [ -z "$(SERVICE)" ] || [ -z "$(COMMAND)" ]; then \
		echo "$(RED)Usage: make exec SERVICE=<service_name> COMMAND='<command>'$(NC)"; \
		echo "Example: make exec SERVICE=web COMMAND='npm install'"; \
	else \
		echo "$(BLUE)Executing '$(COMMAND)' in $(SERVICE) container...$(NC)"; \
		docker compose exec $(SERVICE) $(COMMAND); \
	fi

# Quick shortcuts
npm:
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Usage: make npm CMD='<npm_command>'$(NC)"; \
		echo "Example: make npm CMD='install lodash'"; \
	else \
		echo "$(BLUE)Running npm $(CMD) in web container...$(NC)"; \
		docker compose exec web npm $(CMD); \
	fi

pip:
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Usage: make pip CMD='<pip_command>'$(NC)"; \
		echo "Example: make pip CMD='install requests'"; \
	else \
		echo "$(BLUE)Running pip $(CMD) in API container...$(NC)"; \
		docker compose exec api pip $(CMD); \
	fi

django:
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Usage: make django CMD='<django_command>'$(NC)"; \
		echo "Example: make django CMD='makemigrations'"; \
	else \
		echo "$(BLUE)Running python manage.py $(CMD) in API container...$(NC)"; \
		docker compose exec api python manage.py $(CMD); \
	fi