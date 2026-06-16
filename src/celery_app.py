"""
Celery application configuration.

Sets up the Celery app with Redis as broker, registers periodic
tasks (celery-beat) for cleaning up expired activation tokens.
"""

from celery import Celery
from celery.schedules import crontab

from src.config.settings import settings

# Create Celery application instance with Redis broker.
celery = Celery(
    "cinema",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# ──────────────────────────────────────────────
# Periodic tasks (celery-beat schedule)
# ──────────────────────────────────────────────

celery.conf.beat_schedule = {
    "cleanup-expired-activation-tokens": {
        "task": "src.celery_app.cleanup_expired_activation_tokens",
        "schedule": crontab(minute=0, hour="*/1"),  # Run every hour.
    },
}


@celery.task
def cleanup_expired_activation_tokens() -> str:
    """
    Periodic task to delete expired activation tokens.

    Runs via celery-beat to remove activation tokens that have
    passed their 24-hour expiration window. This keeps the
    activation_tokens table clean and prevents stale data.

    Returns:
        str: Summary message of deleted tokens count.
    """
    import asyncio
    from datetime import datetime, timezone
    from sqlalchemy import delete
    from src.database.session import AsyncSessionLocal
    from src.accounts.models import ActivationTokenModel

    async def _cleanup():
        async with AsyncSessionLocal() as session:
            stmt = delete(ActivationTokenModel).where(
                ActivationTokenModel.expires_at < datetime.now(timezone.utc)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    count = asyncio.run(_cleanup())
    return f"Deleted {count} expired activation tokens."
