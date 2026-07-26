# Multi-stage Dockerfile for FastAPI Online Cinema.
# Uses Python 3.11 slim image with Poetry for dependency management.

FROM python:3.12-slim AS base

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry.
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Set working directory.
WORKDIR /app

# Copy dependency files first for better caching.
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev dependencies in production).
RUN poetry install --no-root --no-dev 2>/dev/null || poetry install --no-root --only main

# Copy application source code.
COPY . .

# Expose application port.
EXPOSE 8000

# Default command: run migrations then start the application.
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
