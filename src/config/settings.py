"""
Application settings module.

Uses Pydantic Settings (v2) to load and validate configuration
from environment variables and .env files. All settings are
centralized here for easy access throughout the application.
"""
import os
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from notifications import EmailSenderInterface
from notifications.emails import get_email_sender
from security.dependencies import get_jwt_auth_manager
from security.interfaces import JWTAuthManagerInterface

# AsyncSession dependency
SessionDep = Annotated[AsyncSession, Depends(get_db)]

# JWTAuthManagerInterface dependency
JWTManagerDep = Annotated[
    JWTAuthManagerInterface, Depends(get_jwt_auth_manager)
]

# EmailSenderInterface dependency
EmailSenderDep = Annotated[
    EmailSenderInterface, Depends(get_email_sender)
]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        POSTGRES_USER: PostgreSQL database username.
        POSTGRES_PASSWORD: PostgreSQL database password.
        POSTGRES_DB: PostgreSQL database name.
        POSTGRES_HOST: PostgreSQL host address.
        POSTGRES_PORT: PostgreSQL port number.
        DATABASE_URL: Full async database connection URL.
        JWT_SECRET_KEY: Secret key for signing JWT tokens.
        JWT_ALGORITHM: Algorithm used for JWT encoding/decoding.
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token TTL in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token TTL in days.
        REDIS_URL: Redis connection URL for Celery broker and caching.
        S3_ENDPOINT_URL: S3-compatible storage endpoint (MinIO).
        S3_ACCESS_KEY: S3 access key.
        S3_SECRET_KEY: S3 secret key.
        S3_BUCKET_NAME: S3 bucket name for file storage.
        STRIPE_SECRET_KEY: Stripe API secret key.
        STRIPE_WEBHOOK_SECRET: Stripe webhook signing secret.
        SMTP_HOST: SMTP server host for sending emails.
        SMTP_PORT: SMTP server port.
        SMTP_USER: SMTP authentication username.
        SMTP_PASSWORD: SMTP authentication password.
        EMAIL_FROM: Default sender email address.
        APP_HOST: Application host address.
        APP_PORT: Application port number.
        APP_BASE_URL: Base URL for generating links (activation, password reset).
        DEBUG: Debug mode flag.
    """

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT", 5432)
    DATABASE_URL: str = (
        f"postgresql+asyncpg://{POSTGRES_USER}"
        f":{POSTGRES_PASSWORD}@{POSTGRES_HOST}"
        f":{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # S3 / MinIO
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "cinema-bucket")

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

    # Email / SMTP
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = os.getenv("SMTP_PORT", 587)
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@cinema.com")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", True)

    # Application
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = os.getenv("APP_PORT", 8000)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    DEBUG: bool = os.getenv("DEBUG", True)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance used throughout the application.
settings = Settings()
