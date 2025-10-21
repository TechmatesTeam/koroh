#!/bin/bash

# Koroh Platform Development Setup Script

set -e

echo "🚀 Setting up Koroh Platform development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created. Please review and update the values.${NC}"
    else
        echo -e "${RED}❌ .env.example file not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Build Docker images
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker compose build

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Run initial migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
docker compose exec api python manage.py migrate

# Install frontend dependencies
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
docker compose exec web npm install

# Create superuser (optional)
echo -e "${YELLOW}👤 Would you like to create a Django superuser? (y/n)${NC}"
read -r create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    docker compose exec api python manage.py createsuperuser
fi

echo -e "${GREEN}🎉 Development environment setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Access URLs:${NC}"
echo -e "  Frontend:    http://localhost:3000"
echo -e "  API:         http://localhost:8000"
echo -e "  PgAdmin:     http://localhost:5050"
echo -e "  MailHog:     http://localhost:8025"
echo -e "  Prometheus:  http://localhost:9090"
echo -e "  Grafana:     http://localhost:3001"
echo -e "  Flower:      http://localhost:5555"
echo ""
echo -e "${BLUE}🛠️  Useful commands:${NC}"
echo -e "  make help           - Show all available commands"
echo -e "  make logs           - Show logs for all services"
echo -e "  make web-shell      - Open shell in web container"
echo -e "  make api-shell      - Open Django shell"
echo -e "  make db-shell       - Open PostgreSQL shell"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"