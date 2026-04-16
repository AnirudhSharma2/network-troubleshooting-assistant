"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Network Troubleshooting Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./network_troubleshooter.db"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # AI Provider: "mock" or "openai" (extendable)
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None

    # Admin bootstrap secret — set this env var to enable POST /api/admin/bootstrap
    ADMIN_BOOTSTRAP_KEY: Optional[str] = None

    # CORS — allow deployed frontend origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://netassist-debug-fyp.vercel.app",
    ]

    # Port for Render deployment
    PORT: int = int(os.environ.get("PORT", "8000"))

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
