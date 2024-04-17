# FastAPI News API Backend

## Overview

A FastAPI backend that integrates with NewsAPI to fetch and manage news articles. Features OAuth2 authentication, database integration, and Docker support.

## Key Features

- FastAPI with OAuth2 authentication (JWT tokens)
- NewsAPI integration with multiple endpoints
- PostgreSQL/SQLite database storage
- Docker and docker-compose support
- Comprehensive testing with pytest
- Ruff linting and code formatting

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)

### Setup

```bash
# Clone and install
git clone <repository-url>
cd fastapi-project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
# Create .env with NEWS_API_KEY, DATABASE_URL, SECRET_KEY

# Run the application
uvicorn main:app --reload
```

### Docker

```bash
docker-compose up --build
```

## API Endpoints

- `GET /news` - Fetch all news with pagination
- `POST /news/save-latest` - Save latest news to database
- `GET /news/headlines/country/{country_code}` - Get headlines by country
- `GET /news/headlines/source/{source_id}` - Get headlines by source
- `GET /news/everything` - Search articles with filters
- `GET /news/sources` - Get available news sources

## Authentication

Use OAuth2 with JWT tokens:

```bash
# Get token
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=client&password=secret"

# Use token
curl -X GET "http://localhost:8000/news/" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

## Development

### Testing

```bash
pytest
pytest --cov=. --cov-report=html
```

### Linting

```bash
./lint.sh
ruff check --fix .
ruff format .
```

## Improvement Recommendations

### Code Quality

- Add comprehensive type annotations
- Implement proper dependency injection patterns
- Create centralized error handling system
- Organize code with layered architecture

### Performance

- Use PostgreSQL with proper indexing for production
- Implement multi-level caching with Redis
- Move long-running tasks to background workers
- Add circuit breakers for external service calls

### Security

- Implement OAuth2 with proper scopes and RBAC
- Add refresh token rotation
- Encrypt sensitive data at rest
- Protect against OWASP Top 10 vulnerabilities

### Testing

- Aim for 90%+ test coverage
- Add integration and contract tests
- Implement performance testing

---

Happy coding! 🚀
