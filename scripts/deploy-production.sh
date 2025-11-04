#!/bin/bash

# Production Deployment Script for Koroh Platform
# This script handles the complete production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_ENV=${DEPLOY_ENV:-production}
BACKUP_ENABLED=${BACKUP_ENABLED:-true}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if production environment file exists
    if [ ! -f ".env.production" ]; then
        log_error "Production environment file (.env.production) not found"
        log_info "Please copy .env.production.example to .env.production and configure it"
        exit 1
    fi
    
    # Check if SSL certificates exist (if HTTPS is enabled)
    if [ -f ".env.production" ] && grep -q "SECURE_SSL_REDIRECT=True" .env.production; then
        if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/private.key" ]; then
            log_warning "SSL certificates not found. HTTPS will not work properly."
            log_info "Please place SSL certificates in nginx/ssl/ directory"
        fi
    fi
    
    log_success "Prerequisites check completed"
}

backup_database() {
    if [ "$BACKUP_ENABLED" = "true" ]; then
        log_info "Creating database backup..."
        
        # Create backup directory
        mkdir -p backups
        
        # Generate backup filename with timestamp
        BACKUP_FILE="backups/koroh_backup_$(date +%Y%m%d_%H%M%S).sql"
        
        # Create database backup
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            --no-owner --no-privileges > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            log_success "Database backup created: $BACKUP_FILE"
        else
            log_error "Database backup failed"
            exit 1
        fi
    else
        log_info "Database backup disabled"
    fi
}

build_images() {
    log_info "Building production images..."
    
    # Build images with production configuration
    docker-compose -f docker-compose.production.yml build --no-cache
    
    if [ $? -eq 0 ]; then
        log_success "Images built successfully"
    else
        log_error "Image build failed"
        exit 1
    fi
}

deploy_services() {
    log_info "Deploying services..."
    
    # Deploy with production configuration
    docker-compose -f docker-compose.production.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "Services deployed successfully"
    else
        log_error "Service deployment failed"
        exit 1
    fi
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations
    docker-compose -f docker-compose.production.yml exec -T api python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

collect_static_files() {
    log_info "Collecting static files..."
    
    # Collect static files
    docker-compose -f docker-compose.production.yml exec -T api python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        log_success "Static files collected"
    else
        log_error "Static file collection failed"
        exit 1
    fi
}

setup_search_index() {
    log_info "Setting up search index..."
    
    # Setup MeiliSearch indexes
    docker-compose -f docker-compose.production.yml exec -T api python manage.py setup_search
    
    if [ $? -eq 0 ]; then
        log_success "Search index setup completed"
    else
        log_warning "Search index setup failed (non-critical)"
    fi
}

health_check() {
    log_info "Performing health checks..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=10
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        # Check API health
        if curl -f -s http://localhost/api/v1/health/ > /dev/null 2>&1; then
            log_success "API health check passed"
            break
        fi
        
        log_info "Waiting for services to be ready... ($elapsed/$timeout seconds)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    if [ $elapsed -ge $timeout ]; then
        log_error "Health check failed - services not ready within $timeout seconds"
        
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            log_info "Rolling back deployment..."
            rollback_deployment
        fi
        
        exit 1
    fi
    
    # Additional health checks
    log_info "Running additional health checks..."
    
    # Check database connectivity
    docker-compose -f docker-compose.production.yml exec -T api python manage.py check --deploy
    
    # Check Celery workers
    docker-compose -f docker-compose.production.yml exec -T celery-worker celery -A koroh_platform inspect ping
    
    log_success "All health checks passed"
}

rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f docker-compose.production.yml down
    
    # Restore from backup if available
    if [ "$BACKUP_ENABLED" = "true" ]; then
        LATEST_BACKUP=$(ls -t backups/koroh_backup_*.sql 2>/dev/null | head -n1)
        if [ -n "$LATEST_BACKUP" ]; then
            log_info "Restoring from backup: $LATEST_BACKUP"
            # Restore database from backup
            docker-compose -f docker-compose.production.yml up -d postgres
            sleep 10
            docker-compose -f docker-compose.production.yml exec -T postgres psql \
                -U "${POSTGRES_USER}" \
                -d "${POSTGRES_DB}" < "$LATEST_BACKUP"
        fi
    fi
    
    log_warning "Rollback completed"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old images (keep last 3 versions)
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        grep koroh | sort -k2 -r | tail -n +4 | awk '{print $1}' | \
        xargs -r docker rmi
    
    log_success "Cleanup completed"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Ensure monitoring services are running
    docker-compose -f docker-compose.production.yml up -d prometheus grafana
    
    # Wait for services to be ready
    sleep 30
    
    # Import Grafana dashboards
    if command -v curl &> /dev/null; then
        log_info "Importing Grafana dashboards..."
        # Add dashboard import logic here if needed
    fi
    
    log_success "Monitoring setup completed"
}

main() {
    log_info "Starting Koroh Platform production deployment..."
    log_info "Environment: $DEPLOY_ENV"
    
    # Load environment variables
    if [ -f ".env.production" ]; then
        export $(cat .env.production | grep -v '^#' | xargs)
    fi
    
    # Execute deployment steps
    check_prerequisites
    backup_database
    build_images
    deploy_services
    run_migrations
    collect_static_files
    setup_search_index
    setup_monitoring
    health_check
    cleanup_old_images
    
    log_success "🎉 Koroh Platform deployed successfully!"
    log_info "Frontend: https://$(echo $DJANGO_ALLOWED_HOSTS | cut -d',' -f1)"
    log_info "API: https://api.$(echo $DJANGO_ALLOWED_HOSTS | cut -d',' -f1)"
    log_info "Monitoring: https://monitoring.$(echo $DJANGO_ALLOWED_HOSTS | cut -d',' -f1)"
    
    # Show service status
    log_info "Service Status:"
    docker-compose -f docker-compose.production.yml ps
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"