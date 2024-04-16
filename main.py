import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, News
from auth import verify_token
from core.security import create_access_token
import httpx
import asyncio
import logging
from aiocache import cached
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import select
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import random
import uuid
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware
from api.endpoints import news
from core.config import settings
from db.session import init_db


# Configure logging based on environment settings
log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)


app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*", "localhost"])

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

NEWS_API_URL = os.getenv("NEWS_API_URL", "https://newsapi.org/v2")


NEWS_API_KEYS = [
    os.getenv("NEWS_API_KEY", "your_newsapi_key"),
    os.getenv("NEWS_API_KEY_2", "your_second_newsapi_key"),
    os.getenv("NEWS_API_KEY_3", "your_third_newsapi_key"),
]

def get_random_api_key():
    return random.choice(NEWS_API_KEYS)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception: {exc} (Error ID: {error_id})")
    logger.exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "message": "An internal server error occurred.",
            "error_id": error_id,
            "details": str(exc) if settings.DEBUG else None
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
        headers=exc.headers,
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):

    try:
        redis_client = redis.from_url("redis://localhost")
        await FastAPILimiter.init(redis_client)
        logger.info("Rate limiter initialized with Redis")
    except Exception as e:
        logger.warning(f"Failed to initialize rate limiter: {e}")


    init_db()

    yield


    logger.info("Shutting down application")


app.router.lifespan_context = lifespan

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Backend!"}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):

    if form_data.username == "client" and form_data.password == "secret":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


app.include_router(news.router, prefix="/news", tags=["News"])