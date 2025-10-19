# Koroh Platform Docker Management

.PHONY: help build up down restart logs clean dev prod

# Default target
help:
	@echo "Koroh Platform Docker Commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services in development mode"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - Show logs for all services"
	@echo "  clean     - Remove all containers, volumes, and images"
	@echo "  dev       - Start development environment"
	@echo "  prod      - Start production environment"
	@echo "  api-shell - Open Django shell"
	@echo "  db-shell  - Open PostgreSQL shell"
	@echo "  test      - Run tests"

# Build all images
build:
	docker-compose build

# Start development environment
dev: up

# Start all services
up:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API: http://localhost:8000"
	@echo "  PgAdmin: http://localhost:5050"
	@echo "  MailHog: http://localhost:8025"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3001"

# Stop all services
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# Show logs
logs:
	docker-compose logs -f

# Start production environment
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Clean up everything
clean:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

# Django shell
api-shell:
	docker-compose exec api python manage.py shell

# Database shell
db-shell:
	docker-compose exec postgres psql -U koroh_user -d koroh_db

# Run tests
test:
	docker-compose exec api python manage.py test
	docker-compose exec web npm test

# Database migrations
migrate:
	docker-compose exec api python manage.py migrate

# Create superuser
createsuperuser:
	docker-compose exec api python manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose exec api python manage.py collectstatic --noinput