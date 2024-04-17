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
