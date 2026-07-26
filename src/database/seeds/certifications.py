"""
Seed default movie certifications.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.seeds.helpers import insert_if_not_exists
from src.movies.models.certification import CertificationModel


DEFAULT_CERTIFICATIONS = [
    "G",
    "PG",
    "PG-13",
    "R",
    "NC-17",
    "TV-G",
    "TV-PG",
    "TV-14",
    "TV-MA",
    "Approved",
    "Passed",
    "Unrated"
]


async def seed_certifications(session: AsyncSession) -> None:
    """Seed default movie certifications."""
    values = [
        {"name": certification}
        for certification in DEFAULT_CERTIFICATIONS
    ]

    await insert_if_not_exists(
        session=session,
        model=CertificationModel,
        values=values
    )
