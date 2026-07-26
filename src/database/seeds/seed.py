"""
Database seed entry point.

Runs all database seeders in the correct order.
"""

import asyncio
import logging

from src.database import models  # noqa: F401, F403
from src.database.session import AsyncSessionLocal
from src.database.seeds.groups import seed_groups
from src.database.seeds.certifications import seed_certifications
from src.database.seeds.genres import seed_genres
from src.database.seeds.movies import seed_movies


logger = logging.getLogger(__name__)

SEEDERS = [
    seed_groups,
    seed_certifications,
    seed_genres,
    seed_movies
]


async def seed_database() -> None:
    """
    Run all database seeders in order.
    """

    async with AsyncSessionLocal() as session:
        try:
            for seeder in SEEDERS:
                logger.info("Running %s", seeder.__name__)
                await seeder(session)

            logger.info("Database seeding completed successfully.")

            await session.commit()

        except Exception:
            await session.rollback()
            raise


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
