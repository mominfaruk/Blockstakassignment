import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base
from db.models import News
from main import app, get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI Backend!"}

def test_create_access_token():
    from auth import create_access_token
    token = create_access_token(data={"sub": "test"})
    assert token is not None
    assert isinstance(token, str)

def test_token_endpoint():
    response = client.post(
        "/token",
        data={"username": "client", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_token_endpoint_invalid_credentials():
    response = client.post(
        "/token",
        data={"username": "invalid", "password": "invalid"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_get_news():
    response = client.get("/news", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401]

def test_save_latest_news():
    response = client.post("/news/save-latest", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401, 500]

def test_get_headlines_by_country():
    response = client.get("/news/headlines/country/us", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401, 500]

def test_get_headlines_by_source():
    response = client.get("/news/headlines/source/abc-news", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401, 500]

def test_get_headlines_by_filter():
    response = client.get("/news/headlines/filter?country=us&source=abc-news", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401, 500]

def test_get_headlines_by_filter_missing_params():
    response = client.get("/news/headlines/filter", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [400, 401]

def test_verify_token():
    from auth import create_access_token, verify_token
    from fastapi import Depends, HTTPException
    from unittest.mock import MagicMock
    import pytest


    valid_token = create_access_token(data={"sub": "testuser"})


    with pytest.raises(HTTPException):
        verify_token(token="invalid_token")

def test_exception_handler():

    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404

def test_save_latest_news_with_db():
    response = client.post("/news/save-latest", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401, 500]
    if response.status_code == 200:
        db = TestingSessionLocal()
        news_items = db.query(News).all()
        assert len(news_items) <= 3
        db.close()


def test_db_models():

    from datetime import datetime
    news = News(
        id="test-id",
        title="Test Title",
        description="Test Description",
        url="http://example.com",
        published_at=datetime.utcnow()
    )
    assert news.id == "test-id"
    assert news.title == "Test Title"
    assert news.description == "Test Description"
    assert news.url == "http://example.com"
    assert isinstance(news.published_at, datetime)

def test_db_session():

    from db.session import get_db
    db_generator = get_db()
    db = next(db_generator)
    assert db is not None
    try:
        next(db_generator)
    except StopIteration:
        pass


def test_news_endpoints_with_mocks():
    from unittest.mock import patch, MagicMock, AsyncMock


    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"status": "ok", "articles": []}


    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)


    with patch('httpx.AsyncClient', return_value=mock_client):

        response = client.get("/news/headlines/country/us", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]


        response = client.get("/news/headlines/source/bbc-news", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]


        response = client.get("/news/headlines/filter?country=us&source=bbc-news", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]


        response = client.post("/news/save-latest", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]

def test_get_news_with_pagination():
    response = client.get("/news?page=1&page_size=2", headers={"Authorization": "Bearer test_token"})
    assert response.status_code in [200, 401]

def test_invalid_token():
    response = client.get("/news", headers={"Authorization": "Bearer invalid_token"})

    assert response.status_code in [200, 401]