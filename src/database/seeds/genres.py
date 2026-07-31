"""
Seed default movie genres.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.seeds.helpers import insert_if_not_exists
from src.movies.models.genre import GenreModel


DEFAULT_GENRES = [
    "Action",
    "Adventure",
    "Animation",
    "Biography",
    "Comedy",
    "Crime",
    "Drama",
    "Fantasy",
    "History",
    "Horror",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller"
]


async def seed_genres(session: AsyncSession) -> None:
    """Seed default movie genres table."""
    values = [
        {"name": genre}
        for genre in DEFAULT_GENRES
    ]

    await insert_if_not_exists(
        session=session,
        model=GenreModel,
        values=values
    )
