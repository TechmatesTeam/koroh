# Docker Setup for Koroh Platform

This document provides comprehensive instructions for running the Koroh Platform using Docker.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Make (for using Makefile commands)

## Quick Start

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <repository-url>
   cd koroh-platform
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Run the setup script**
   ```bash
   ./scripts/setup-dev.sh
   ```

   Or manually:
   ```bash
   make build
   make up
   make api-migrate
   make web-install
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - PgAdmin: http://localhost:5050
   - MailHog: http://localhost:8025

## Available Services

| Service | Container Name | Port | Description |
|---------|----------------|------|-------------|
| web | koroh_web | 3000 | Next.js Frontend |
| api | koroh_api | 8000 | Django Backend API |
| postgres | koroh_postgres | 5432 | PostgreSQL Database |
| redis | koroh_redis | 6379 | Redis Cache |
| meilisearch | koroh_meilisearch | 7700 | Search Engine |
| celery_worker | koroh_celery_worker | - | Background Tasks |
| celery_beat | koroh_celery_beat | - | Task Scheduler |
| celery_flower | koroh_celery_flower | 5555 | Task Monitoring |
| nginx | koroh_nginx | 80/443 | Reverse Proxy |
| pgadmin | koroh_pgadmin | 5050 | Database Admin |
| mailhog | koroh_mailhog | 8025 | Email Testing |
| prometheus | koroh_prometheus | 9090 | Metrics Collection |
| grafana | koroh_grafana | 3001 | Monitoring Dashboard |

## Makefile Commands

### Environment Management
```bash
make help          # Show all available commands
make build         # Build all Docker images
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # Show logs for all services
make clean         # Remove all containers and volumes
make dev           # Start development environment
make prod          # Start production environment
make status        # Show service status
```

### Frontend (Web) Commands
```bash
make web-shell     # Open shell in web container
make web-install   # Install npm dependencies
make web-build     # Build Next.js application
make web-test      # Run frontend tests
make web-lint      # Run frontend linting
make web-logs      # Show web container logs

# Quick npm commands
make npm CMD='install lodash'    # Install npm package
make npm CMD='run build'         # Run npm script
```

### Backend (API) Commands
```bash
make api-shell     # Open Django shell
make api-bash      # Open bash shell in API container
make api-migrate   # Run Django migrations
make api-test      # Run backend tests
make api-logs      # Show API container logs
make api-superuser # Create Django superuser
make api-static    # Collect static files

# Quick Django commands
make django CMD='makemigrations'     # Create migrations
make django CMD='createsuperuser'    # Create superuser
make django CMD='collectstatic'      # Collect static files
```

### Database Commands
```bash
make db-shell      # Open PostgreSQL shell
make db-migrate    # Run database migrations
make db-reset      # Reset database (WARNING: destroys data)
make db-backup     # Create database backup
make db-restore    # Restore database from backup
make db-logs       # Show database logs
```

### Celery Commands
```bash
make celery-logs   # Show Celery worker logs
make celery-status # Check Celery worker status
make celery-purge  # Purge all Celery tasks
make flower        # Open Celery Flower monitoring
```

### Monitoring Commands
```bash
make monitor       # Show all monitoring URLs
make prometheus    # Open Prometheus
make grafana       # Open Grafana
make mailhog       # Open MailHog
```

## Development Workflow

### Frontend Development
```bash
# Start the development environment
make up

# Install new npm packages
make npm CMD='install package-name'

# Run tests
make web-test

# Access the web container shell
make web-shell

# View logs
make web-logs
```

### Backend Development
```bash
# Create and run migrations
make django CMD='makemigrations'
make api-migrate

# Access Django shell
make api-shell

# Run tests
make api-test

# Create superuser
make api-superuser

# View logs
make api-logs
```

### Database Operations
```bash
# Access database shell
make db-shell

# Create backup
make db-backup

# Reset database (development only)
make db-reset
```

## Production Deployment

1. **Update environment variables for production**
   ```bash
   # Edit .env file with production values
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=your-domain.com
   # ... other production settings
   ```

2. **Start production environment**
   ```bash
   make prod
   ```

3. **The production setup includes:**
   - Optimized Docker images
   - Gunicorn for Django
   - Nginx reverse proxy
   - SSL termination (configure certificates)
   - Production-ready logging

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the port
   lsof -i :3000
   
   # Update port in .env file
   WEB_PORT=3001
   ```

2. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Database connection issues**
   ```bash
   # Check database status
   make status
   
   # View database logs
   make db-logs
   
   # Reset database
   make db-reset
   ```

4. **Frontend build issues**
   ```bash
   # Clear node_modules and reinstall
   make web-shell
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Container not starting**
   ```bash
   # View specific service logs
   docker compose logs service-name
   
   # Rebuild specific service
   docker compose build service-name
   ```

### Debugging

1. **Access container shells**
   ```bash
   make web-shell     # Frontend container
   make api-bash      # Backend container
   make db-shell      # Database shell
   ```

2. **View logs**
   ```bash
   make logs          # All services
   make web-logs      # Frontend only
   make api-logs      # Backend only
   make db-logs       # Database only
   ```

3. **Check service status**
   ```bash
   make status        # Service status
   make ps            # Running containers
   ```

## Environment Variables

Key environment variables for Docker setup:

### Database
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `DATABASE_URL`: Full database connection string

### Frontend
- `NEXT_PUBLIC_API_URL`: API endpoint URL
- `NEXTAUTH_SECRET`: NextAuth secret key
- `NEXTAUTH_URL`: Frontend URL

### Backend
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Debug mode (True/False)
- `DJANGO_ALLOWED_HOSTS`: Allowed hosts
- `DJANGO_CORS_ALLOWED_ORIGINS`: CORS origins

### Ports
- `WEB_PORT`: Frontend port (default: 3000)
- `API_PORT`: Backend port (default: 8000)
- `POSTGRES_PORT`: Database port (default: 5432)

## File Structure

```
koroh-platform/
├── docker-compose.yml          # Main Docker Compose file
├── docker-compose.override.yml # Development overrides
├── docker-compose.prod.yml     # Production overrides
├── Makefile                    # Command shortcuts
├── .env.example               # Environment template
├── scripts/
│   └── setup-dev.sh          # Development setup script
├── web/
│   ├── Dockerfile            # Production Dockerfile
│   ├── Dockerfile.dev        # Development Dockerfile
│   └── .dockerignore         # Docker ignore file
└── api/
    └── Dockerfile            # API Dockerfile
```

## Support

For issues and questions:
1. Check the logs: `make logs`
2. Review this documentation
3. Check Docker and Docker Compose versions
4. Ensure all required ports are available
5. Verify environment variables in `.env` file