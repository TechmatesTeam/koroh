# Koroh Platform

An AI-powered professional networking platform built with Django, Next.js, and AWS Bedrock.

## Architecture

- **Frontend**: Next.js/React (web/)
- **Backend**: Django REST API (api/)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Search**: MeiliSearch
- **Task Queue**: Celery
- **Monitoring**: Prometheus + Grafana
- **Reverse Proxy**: Nginx

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Development Setup

1. Clone the repository and navigate to the project directory

2. Copy and configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the development environment:

   ```bash
   make dev
   # or
   docker-compose up -d
   ```

4. Access the services:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - PgAdmin: http://localhost:5050
   - MailHog: http://localhost:8025
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001

### Production Setup

1. Configure production environment variables in `.env`

2. Start production environment:
   ```bash
   make prod
   # or
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## Services

### Core Services

- **api**: Django backend API
- **web**: Next.js frontend application
- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **meilisearch**: Full-text search engine
- **nginx**: Reverse proxy and load balancer

### Background Processing

- **celery_worker**: Celery task workers
- **celery_beat**: Celery periodic task scheduler

### Monitoring & Development

- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards
- **mailhog**: Email testing (development)
- **pgadmin**: Database administration

## Development Commands

```bash
# Start development environment
make dev

# View logs
make logs

# Run database migrations
make migrate

# Create Django superuser
make createsuperuser

# Access Django shell
make api-shell

# Access database shell
make db-shell

# Run tests
make test

# Stop all services
make down

# Clean up everything
make clean
```

## Environment Variables

Key environment variables in `.env`:

- `POSTGRES_*`: Database configuration
- `REDIS_*`: Redis configuration
- `DJANGO_*`: Django settings
- `AWS_*`: AWS Bedrock configuration
- `NEXT_PUBLIC_*`: Next.js public variables

## Project Structure

```
koroh-platform/
├── api/                    # Django backend
├── web/                    # Next.js frontend
├── nginx/                  # Nginx configuration
├── monitoring/             # Prometheus & Grafana config
├── scripts/                # Database and utility scripts
├── docker-compose.yml      # Main Docker Compose file
├── docker-compose.override.yml  # Development overrides
├── docker-compose.prod.yml # Production overrides
├── .env                    # Environment variables
└── Makefile               # Development commands
```

## Next Steps

1. Implement Django backend (Task 2)
2. Set up Next.js frontend (Task 8)
3. Configure AWS Bedrock integration (Task 4)
4. Implement core features (Tasks 3, 5, 6)

## Contributing

1. Follow the task-based development approach outlined in the specs
2. Use the provided Docker environment for development
3. Run tests before submitting changes
4. Follow the established code structure and patterns
