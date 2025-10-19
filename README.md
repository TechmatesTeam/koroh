# Koroh Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/TechmatesTeam/koroh)](https://github.com/TechmatesTeam/koroh/issues)
[![GitHub stars](https://img.shields.io/github/stars/TechmatesTeam/koroh)](https://github.com/TechmatesTeam/koroh/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/TechmatesTeam/koroh)](https://github.com/TechmatesTeam/koroh/network)

An AI-powered professional networking platform that helps users build meaningful professional connections through intelligent matching and personalized recommendations. Built with Django, Next.js, and AWS Bedrock.

## 🌟 Features

- **AI-Powered Matching**: Intelligent connection recommendations using AWS Bedrock
- **Professional Profiles**: Comprehensive user profiles with skills, experience, and goals
- **Smart Networking**: Personalized networking suggestions and introductions
- **Real-time Messaging**: Secure communication between professionals
- **Event Management**: Professional events and networking opportunities
- **Analytics Dashboard**: Insights into networking activities and connections

## 🏗️ Project Information

- **Repository**: [https://github.com/TechmatesTeam/koroh](https://github.com/TechmatesTeam/koroh)
- **Organization**: [Techmates Team](https://github.com/TechmatesTeam)
- **Project Lead**: Emmanuel Odero ([@Emmanuel-Odero](https://github.com/Emmanuel-Odero))
- **Contact**: emmanuelodero@techmates.team

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

## 🤝 Contributing

We welcome contributions from the community! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Development setup and workflow
- Code style and standards
- Pull request process
- Issue reporting

### Quick Start for Contributors

1. Fork the repository
2. Clone your fork i.e: `git clone https://github.com/TechmatesTeam/koroh`
3. Set up development environment: `make dev`
4. Create a feature branch: `git checkout -b feature/your-feature`
5. Make your changes and add tests
6. Submit a pull request

See our [Contributors Guide](CONTRIBUTORS.md) for more information.

## 📋 Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Contributors](CONTRIBUTORS.md)
- [License](LICENSE)

## 🔒 Security

Security is a top priority for Koroh. If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) and report it responsibly to emmanuelodero@techmates.team.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/TechmatesTeam/koroh/issues)
- **Discussions**: [GitHub Discussions](https://github.com/TechmatesTeam/koroh/discussions)
- **Email**: emmanuelodero@techmates.team

## 🙏 Acknowledgments

- All [contributors](CONTRIBUTORS.md) who have helped build Koroh
- The open-source community for the amazing tools and libraries
- AWS for providing the Bedrock AI services

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [Techmates Team](https://github.com/TechmatesTeam)**
