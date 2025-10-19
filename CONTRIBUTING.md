# Contributing to Koroh Platform

Thank you for your interest in contributing to Koroh! This document provides guidelines and information for contributors.

## Project Overview

Koroh is an AI-powered professional networking platform that helps users build meaningful professional connections through intelligent matching and personalized recommendations.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/TechmatesTeam/koroh
   cd koroh
   ```

3. Set up the development environment:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   make dev
   ```

4. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:

```
feat(api): add user profile endpoints
fix(web): resolve login form validation issue
docs: update API documentation
```

### Code Style

#### Python (Django Backend)

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters

#### JavaScript/TypeScript (Next.js Frontend)

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use [Prettier](https://prettier.io/) for code formatting
- Use [ESLint](https://eslint.org/) for linting
- Prefer TypeScript over JavaScript for new code

### Testing

#### Backend Tests

```bash
# Run all tests
make test

# Run specific test file
docker-compose exec api python manage.py test apps.users.tests.test_models

# Run with coverage
docker-compose exec api coverage run --source='.' manage.py test
docker-compose exec api coverage report
```

#### Frontend Tests

```bash
# Run all tests
docker-compose exec web npm test

# Run tests in watch mode
docker-compose exec web npm run test:watch

# Run tests with coverage
docker-compose exec web npm run test:coverage
```

### Database Migrations

When making model changes:

1. Create migrations:

   ```bash
   docker-compose exec api python manage.py makemigrations
   ```

2. Apply migrations:

   ```bash
   docker-compose exec api python manage.py migrate
   ```

3. Include migration files in your commit

## Pull Request Process

1. **Before submitting:**

   - Ensure all tests pass
   - Update documentation if needed
   - Add tests for new functionality
   - Follow the code style guidelines

2. **Pull Request Template:**

   - Use the provided PR template
   - Include a clear description of changes
   - Reference related issues
   - Add screenshots for UI changes

3. **Review Process:**
   - All PRs require at least one review
   - Address review feedback promptly
   - Keep PRs focused and reasonably sized

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots/logs if applicable

### Feature Requests

Use the feature request template and include:

- Clear description of the feature
- Use case and benefits
- Proposed implementation (if any)
- Acceptance criteria

## Development Guidelines

### API Development

- Follow RESTful conventions
- Use proper HTTP status codes
- Include comprehensive error handling
- Document endpoints with OpenAPI/Swagger
- Implement proper authentication/authorization

### Frontend Development

- Use TypeScript for type safety
- Implement responsive design
- Follow accessibility guidelines (WCAG 2.1)
- Optimize for performance
- Use proper error boundaries

### Security

- Never commit sensitive data (API keys, passwords)
- Use environment variables for configuration
- Implement proper input validation
- Follow OWASP security guidelines
- Report security issues privately to emmanuelodero@techmates.team

## Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Write clear commit messages
- Add tests for new functionality
- Update documentation
- Respond to feedback constructively

### For Reviewers

- Be constructive and respectful
- Focus on code quality and maintainability
- Check for security issues
- Verify tests are adequate
- Approve when ready

## Release Process

1. Version bumping follows [Semantic Versioning](https://semver.org/)
2. Releases are created from the `main` branch
3. Release notes are generated automatically
4. Deployment is handled through CI/CD pipeline

## Getting Help

- **Documentation:** Check the [README](README.md) and [docs/](docs/) folder
- **Issues:** Search existing issues before creating new ones
- **Discussions:** Use GitHub Discussions for questions
- **Contact:** Reach out to Emmanuel Odero at emmanuelodero@techmates.team

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## License

By contributing to Koroh, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors are recognized in:

- [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Release notes
- Project documentation

Thank you for contributing to Koroh! 🚀
