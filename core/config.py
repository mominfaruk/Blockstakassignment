from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI News API"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./news.db"
    DATABASE_URL_DOCKER: str = "postgresql://newsuser:Passw0rd!2024@db:5432/newsdb"
    NEWS_API_URL: str = "https://newsapi.org/v2"
    NEWS_API_KEY: str = "your_newsapi_key"
    SECRET_KEY: str = "your_secret_key_here"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = Field(default=False)
    ALLOW_ORIGINS: str = "http://localhost:3000,https://news-frontend.example.com"


    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()