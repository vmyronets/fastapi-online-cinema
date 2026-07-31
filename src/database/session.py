"""
Async database session configuration.

Sets up the SQLAlchemy async engine and session factory using
the DATABASE_URL from application settings. Provides a FastAPI
dependency (`get_db`) that yields an async session per request.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings


# Async SQLAlchemy engine connected to PostgreSQL via asyncpg.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Async session factory bound to the engine.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """
    Declarative base class for all SQLAlchemy ORM models.

    All database models inherit from this class, which provides
    metadata and mapping capabilities for table definitions.
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Yields an `AsyncSession` instance and ensures it is properly
    closed after the request completes.

    Yields:
        AsyncSession: An active async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
