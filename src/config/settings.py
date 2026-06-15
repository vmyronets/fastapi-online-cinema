"""
Application settings module.

Uses Pydantic Settings (v2) to load and validate configuration
from environment variables and .env files. All settings are
centralized here for easy access throughout the application.
"""
import os

from pydantic_settings import BaseSettings


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
        S3_ENDPOINT_URL: S3-compatible storage endpoint (MinIO).
        S3_ACCESS_KEY: S3 access key.
        S3_SECRET_KEY: S3 secret key.
        S3_BUCKET_NAME: S3 bucket name for file storage.
    """

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT", 5432)
    DATABASE_URL: str = (f"postgresql+asyncpg://{POSTGRES_USER}"
                         f":{POSTGRES_PASSWORD}@{POSTGRES_HOST}"
                         f":{POSTGRES_PORT}/{POSTGRES_DB}")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)

    # S3 / MinIO
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "cinema-bucket")


# Singleton settings instance used throughout the application.
settings = Settings()
