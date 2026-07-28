"""
Application settings module.

Uses Pydantic Settings (v2) to load and validate configuration
from environment variables and .env files. All settings are
centralized here for easy access throughout the application.
"""
import os

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"
    POSTGRES_DB: str = "test_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # JWT
    JWT_SECRET_KEY: str = "secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "cinema-bucket"

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"

    # Email / SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cinema.com"
    SMTP_USE_TLS: bool = True

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_BASE_URL: str = "http://localhost:8000"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Singleton settings instance used throughout the application.
settings = Settings()
