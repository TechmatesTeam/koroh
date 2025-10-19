# Changelog

All notable changes to the Koroh Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project structure and Docker infrastructure
- Complete Docker Compose setup with all required services
- Nginx reverse proxy configuration
- Prometheus and Grafana monitoring setup
- Comprehensive project documentation
- Contributing guidelines and code of conduct
- GitHub issue and PR templates
- Security policy and procedures

### Infrastructure

- PostgreSQL database with proper initialization
- Redis cache and message broker
- MeiliSearch for full-text search
- MailHog for email testing in development
- PgAdmin for database management
- Celery for background task processing
- Multi-environment Docker configurations (dev/prod)

### Documentation

- Complete README with setup instructions
- Contributing guidelines with development workflow
- Code of conduct for community standards
- Security policy for vulnerability reporting
- License (MIT) and contributor recognition
- GitHub templates for issues and pull requests

## [0.1.0] - 2024-10-19

### Added

- Initial project setup
- Monorepo structure with web/ and api/ directories
- Docker infrastructure foundation
- Basic project documentation

---

## Release Notes Format

### Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

### Categories

- **Frontend** - Next.js/React changes
- **Backend** - Django API changes
- **Infrastructure** - Docker, deployment, monitoring
- **Documentation** - Docs, README, guides
- **Security** - Security improvements and fixes
- **Performance** - Performance improvements
- **Testing** - Test additions and improvements
