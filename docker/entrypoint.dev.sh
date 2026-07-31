#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding database..."
python -m src.database.seeds.seed

echo "Starting FastAPI development server..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload