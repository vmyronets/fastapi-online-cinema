# Multi-stage Dockerfile for FastAPI Online Cinema.
# Contains the common environment and dependencies shared by all stages.
# Uses Python 3.12 slim image with Poetry for dependency management.

# =============================================================================
# Base image
# =============================================================================
FROM python:3.12-slim AS base

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.4.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN python -m pip install --no-cache-dir poetry==${POETRY_VERSION}

# Set working directory
WORKDIR /app

# Copy dependency files first to maximize Docker layer caching.
COPY pyproject.toml poetry.lock ./

# =============================================================================
# Production stage
# =============================================================================
FROM base AS production

# Install only production dependencies.
RUN poetry install --only main

# Copy application source code.
COPY . .

# Expose application port.
EXPOSE 8000

# Default command: run migrations then start the application.
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]

# =============================================================================
# Development stage
# =============================================================================
FROM base AS development

# Install all dependencies, including development tools.
RUN poetry install

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Test stage
# =============================================================================
FROM base AS test

# Install all dependencies required for testing.
RUN poetry install

COPY . .

CMD ["pytest"]