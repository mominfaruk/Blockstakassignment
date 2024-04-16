# FastAPI News API Backend

## Project Description

This is a FastAPI-based backend application that integrates with the NewsAPI to fetch and manage news articles. It includes features like OAuth2 authentication, database integration, and Dockerization.

## Key Features

- **FastAPI Framework**: High-performance, easy-to-use framework for building APIs
- **OAuth2 Authentication**: Secure API endpoints with JWT tokens
- **NewsAPI Integration**: Fetch latest news from various sources and categories
- **Database Storage**: Store news articles in PostgreSQL (production) or SQLite (development)
- **Docker Support**: Easy deployment with Docker and docker-compose
- **Comprehensive Testing**: Unit tests with pytest and high coverage
- **API Documentation**: Auto-generated with Swagger UI
- **Rate Limiting**: Prevent abuse with Redis-based rate limiting
- **Prometheus Metrics**: Monitor API performance with Prometheus instrumentation
- **Async/Await**: Utilize Python's asynchronous features for improved performance

## Folder Structure

```
fastapi_project/
    __init__.py
    main.py
    api/
        __init__.py
        endpoints/
            __init__.py
            news.py
    core/
        __init__.py
        config.py
        security.py
    db/
        __init__.py
        base.py
        models.py
        session.py
    tests/
        __init__.py
        test_main.py

    Dockerfile
    docker-compose.yml
    README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Docker (optional, for containerization)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd fastapi-project
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add the following:

   ```env
   NEWS_API_KEY=your_newsapi_key
   NEWS_API_URL=https://newsapi.org/v2
   DATABASE_URL=sqlite:///./news.db
   DATABASE_URL_DOCKER=postgresql://newsuser:Passw0rd!2024@db:5432/newsdb
   SECRET_KEY=your_secret_key_here
   LOG_LEVEL=INFO
   DEBUG=false
   ALLOW_ORIGINS=http://localhost:3000,https://news-frontend.example.com
   ```

5. Run the application:

   ```bash
   uvicorn main:app --reload
   ```

6. Access the API at `http://127.0.0.1:8000`.

## How to Run Tests

1. Install test dependencies if not already installed:

   ```bash
   pip install pytest pytest-cov
   ```

2. Run the tests:

   ```bash
   pytest
   ```

3. Generate a coverage report:

   ```bash
   pytest --cov=. --cov-report=html
   ```

4. View the coverage report in the `htmlcov` directory.

## Code Quality

### Linting with Ruff

This project uses Ruff for linting and code formatting. Ruff is a fast Python linter written in Rust that combines the functionality of multiple tools like Flake8, isort, and more.

1. Run the linter:

   ```bash
   ./lint.sh
   ```

2. Fix auto-fixable issues:

   ```bash
   ruff check --fix .
   ```

3. Format code:
   ```bash
   ruff format .
   ```

The linter configuration is defined in `pyproject.toml`.

## How to Use Docker

### Option 1: Using Docker Directly

1. Build the Docker image:

   ```bash
   docker build -t fastapi-news-api .
   ```

2. Run the Docker container:

   ```bash
   docker run -p 8000:8000 -e NEWS_API_KEY=your_newsapi_key fastapi-news-api
   ```

3. Access the API at `http://127.0.0.1:8000`.

### Option 2: Using Docker Compose (Recommended)

1. Ensure Docker and Docker Compose are installed on your system.
2. Update the `.env` file with your NewsAPI key.
3. Run the following command to start the application and PostgreSQL database:
   ```bash
   docker-compose up --build
   ```
4. Access the application at `http://localhost:8000`.

## API Endpoints

### 1. `GET /`

- **Description**: Welcome message.
- **Response**:
  ```json
  { "message": "Welcome to the FastAPI Backend!" }
  ```

### 2. `GET /news`

- **Description**: Fetch all news with pagination.
- **Query Parameters**:
  - `page` (int): Page number (default: 1).
  - `page_size` (int): Number of items per page (default: 10).
- **Authentication**: Bearer token required.

### 3. `POST /news/save-latest`

- **Description**: Fetch the latest news and save the top 3 into the database.
- **Authentication**: Bearer token required.

### 4. `GET /news/headlines/country/{country_code}`

- **Description**: Fetch top headlines by country.
- **Path Parameters**:
  - `country_code` (str): Country code (e.g., `us`, `gb`).
- **Authentication**: Bearer token required.

### 5. `GET /news/headlines/source/{source_id}`

- **Description**: Fetch top headlines by source.
- **Path Parameters**:
  - `source_id` (str): Source ID (e.g., `abc-news`).
- **Authentication**: Bearer token required.

### 6. `GET /news/headlines/filter`

- **Description**: Fetch top headlines by filtering both country and source.
- **Query Parameters**:
  - `country` (str): Country code.
  - `source` (str): Source ID.
- **Authentication**: Bearer token required.

### 7. `GET /news/everything`

- **Description**: Search for news articles with keywords and filters.
- **Query Parameters**:
  - `q` (str, required): Keywords or phrases to search for.
  - `from` (str, optional): A date for the oldest article allowed (format: YYYY-MM-DD).
  - `to` (str, optional): A date for the newest article allowed (format: YYYY-MM-DD).
  - `language` (str, optional): 2-letter ISO-639-1 language code (e.g., 'en', 'fr').
  - `sortBy` (str, optional): Order to sort articles ('relevancy', 'popularity', 'publishedAt').
  - `page` (int, optional): Page number (default: 1).
  - `pageSize` (int, optional): Number of results per page (default: 20, max: 100).
- **Authentication**: Bearer token required.

### 8. `GET /news/sources`

- **Description**: Get available news sources/publishers.
- **Query Parameters**:
  - `category` (str, optional): News category (e.g., 'business', 'technology').
  - `language` (str, optional): 2-letter ISO-639-1 language code (e.g., 'en', 'fr').
  - `country` (str, optional): 2-letter ISO-3166-1 country code (e.g., 'us', 'gb').
- **Authentication**: Bearer token required.

## Authentication

The API uses OAuth2 with JWT tokens for authentication. To get a token, use the `/token` endpoint:

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=client&password=secret"
```

The response will contain an access token that you can use to authenticate requests to protected endpoints:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Use this token in the Authorization header for subsequent requests:

```bash
curl -X GET "http://localhost:8000/news/" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

Error responses include a detail message explaining the error.

## Performance Considerations

- **Connection Pooling**: The application uses SQLAlchemy's connection pooling for efficient database connections
- **Async/Await**: Utilizes FastAPI's asynchronous capabilities for improved performance
- **Rate Limiting**: Prevents abuse with Redis-based rate limiting
- **Caching**: Implements caching for frequently accessed endpoints

## Monitoring and Logging

- **Prometheus Metrics**: API performance metrics are exposed at `/metrics`
- **Structured Logging**: Comprehensive logging with configurable log levels
- **Request/Response Logging**: All requests and responses are logged for debugging

## Future Improvements

- Add user management with registration and profile management
- Implement more sophisticated caching strategies
- Add support for WebSockets for real-time news updates
- Enhance test coverage and add integration tests
- Implement CI/CD pipeline for automated testing and deployment

## Codebase Improvement Recommendations

The following recommendations aim to enhance the quality, performance, and maintainability of the codebase:

### Code Quality and Structure

1. **Type Annotations**:

   - Add comprehensive type annotations to all functions and methods
   - Use generic types for collections to improve type safety
   - Consider using Pydantic models for all data structures

2. **Dependency Injection**:

   - Refactor to use proper dependency injection patterns
   - Move `Depends()` calls out of function parameter defaults
   - Create reusable dependencies for common operations

3. **Error Handling**:

   - Implement a centralized error handling system
   - Use custom exception classes for different error types
   - Use `raise ... from err` pattern to preserve exception context
   - Define error constants instead of using magic numbers

4. **Code Organization**:
   - Split large modules into smaller, focused ones
   - Implement a layered architecture (controllers, services, repositories)
   - Use domain-driven design principles for complex features

### Performance Optimizations

1. **Database Improvements**:

   - Migrate from SQLite to PostgreSQL for production use
   - Implement database indexing for frequently queried fields
   - Use connection pooling with proper sizing based on load
   - Implement database partitioning for large datasets

2. **Caching Strategy**:

   - Implement a multi-level caching strategy
   - Use Redis for distributed caching with proper TTL settings
   - Implement cache invalidation patterns for data consistency
   - Consider using cache-aside pattern for frequently accessed data

3. **Asynchronous Processing**:
   - Move long-running tasks to background workers
   - Implement a task queue system (Celery, RQ, or FastAPI's background tasks)
   - Use connection pooling for external API calls
   - Implement circuit breakers for external service calls

### Scalability and Reliability

1. **Horizontal Scaling**:

   - Make the application stateless for horizontal scaling
   - Use a load balancer for distributing traffic
   - Implement sticky sessions if needed
   - Consider using Kubernetes for orchestration

2. **Monitoring and Observability**:

   - Enhance logging with structured logs
   - Implement distributed tracing (OpenTelemetry)
   - Set up comprehensive metrics collection
   - Create dashboards for key performance indicators

3. **Resilience**:
   - Implement retry mechanisms with exponential backoff
   - Add circuit breakers for external dependencies
   - Implement graceful degradation for non-critical features
   - Set up proper health checks and readiness probes

### Security Enhancements

1. **Authentication and Authorization**:

   - Implement OAuth2 with proper scopes
   - Add role-based access control (RBAC)
   - Use refresh tokens with proper rotation
   - Implement API rate limiting per user

2. **Data Protection**:
   - Encrypt sensitive data at rest
   - Implement proper input validation and sanitization
   - Add protection against common web vulnerabilities (OWASP Top 10)
   - Implement proper secrets management

### Testing Strategy

1. **Test Coverage**:

   - Aim for 90%+ test coverage
   - Implement property-based testing for complex logic
   - Add integration tests for critical paths
   - Implement contract tests for external dependencies

2. **Test Automation**:
   - Set up continuous integration with automated testing
   - Implement pre-commit hooks for code quality checks
   - Add performance testing for critical endpoints
   - Implement security scanning in the CI pipeline

---

Happy coding! 🚀
