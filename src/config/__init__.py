"""
Configuration module for the FastAPI Online Cinema application.

Provides centralized settings management using Pydantic Settings,
loading configuration from environment variables and .env files.
"""

from src.config.settings import settings

__all__ = ["settings"]
