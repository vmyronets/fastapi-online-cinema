"""
Application settings module.

Uses Pydantic Settings (v2) to load and validate configuration
from environment variables and .env files. All settings are
centralized here for easy access throughout the application.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


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
    """

    # Database
    POSTGRES_USER: str = Field(default="cinema_user")
    POSTGRES_PASSWORD: str = Field(default="cinema_password")
    POSTGRES_DB: str = Field(default="cinema_db")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(
        default=f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


# Singleton settings instance used throughout the application.
settings = Settings()
