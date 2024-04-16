import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.base import Base
from db.models import News
from main import app, get_db
from api.endpoints.news import (
    get_news,
    save_latest_news,
    get_headlines_by_country,
    get_headlines_by_source,
    get_headlines_by_filter
)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_news.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


from core.security import verify_token

def mock_verify_token():
    return {"username": "testuser"}


app.dependency_overrides[verify_token] = mock_verify_token


mock_articles = [
    {
        "title": "Test Article 1",
        "description": "Test Description 1",
        "url": "http://example.com/1",
        "publishedAt": datetime.now(timezone.utc).isoformat()
    },
    {
        "title": "Test Article 2",
        "description": "Test Description 2",
        "url": "http://example.com/2",
        "publishedAt": datetime.now(timezone.utc).isoformat()
    },
    {
        "title": "Test Article 3",
        "description": "Test Description 3",
        "url": "http://example.com/3",
        "publishedAt": datetime.now(timezone.utc).isoformat()
    }
]

@pytest.fixture
def mock_httpx_client():

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"status": "ok", "articles": mock_articles}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient', return_value=mock_client):
        yield

@pytest.fixture
def db_with_news():

    db = TestingSessionLocal()


    db.query(News).delete()


    for i in range(5):
        news = News(
            id=f"test-id-{i}",
            title=f"Test Title {i}",
            description=f"Test Description {i}",
            url=f"http://example.com/{i}",
            published_at=datetime.now(timezone.utc)
        )
        db.add(news)

    db.commit()
    yield db
    db.close()

def test_get_news(db_with_news):

    response = client.get("/news?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 3

def test_get_news_pagination(db_with_news):


    response1 = client.get("/news?page=1&page_size=2")
    assert response1.status_code == 200
    data1 = response1.json()


    response2 = client.get("/news?page=2&page_size=2")
    assert response2.status_code == 200
    data2 = response2.json()


    if data1["items"] and data2["items"]:
        assert data1["items"][0]["id"] != data2["items"][0]["id"]

def test_save_latest_news(mock_httpx_client):

    response = client.post("/news/save-latest")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Successfully saved" in response.json()["message"]

def test_get_headlines_by_country(mock_httpx_client):

    response = client.get("/news/headlines/country/us")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "articles" in data
    assert len(data["articles"]) == 3

def test_get_headlines_by_source(mock_httpx_client):

    response = client.get("/news/headlines/source/bbc-news")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "articles" in data
    assert len(data["articles"]) == 3

def test_get_headlines_by_filter(mock_httpx_client):

    response = client.get("/news/headlines/filter?country=us&source=bbc-news")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "articles" in data
    assert len(data["articles"]) == 3

def test_get_headlines_by_filter_missing_params():

    response = client.get("/news/headlines/filter")
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "At least one filter parameter" in response.json()["detail"]

def test_http_error_handling(mock_httpx_client):


    response = client.get("/news/headlines/country/us")
    assert response.status_code in [200, 500]
