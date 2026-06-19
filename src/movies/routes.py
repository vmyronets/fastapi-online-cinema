"""
API routes for the movies module.

Provides endpoints for browsing movies, CRUD operations (moderator),
genres, comments, ratings, favorites, and likes/dislikes.
"""

from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from movies.models.movie import MovieModel
from movies.schemas import MovieListResponseSchema
from src.accounts.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum
)

router = APIRouter(prefix="/movies", tags=["Movies"])


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

async def _require_moderator(db: AsyncSession, user_id: int) -> None:
    """
    Verify the user has MODERATOR or ADMIN privileges.

    Args:
        db: Async database session.
        user_id: The user's ID to check.

    Raises:
        HTTPException: If the user is not a moderator or admin.
    """
    stmt = (
        select(UserGroupModel).join(UserModel).where(UserModel.id == user_id)
    )
    result = await db.execute(stmt)
    group = result.scalars().first()
    if not group or group.name == UserGroupEnum.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin privileges required."
        )


def _build_movie_list_response(movie: MovieModel) -> MovieListResponseSchema:
    """
    Build a MovieListResponseSchema from a MovieModel instance.

    Args:
        movie: The MovieModel ORM instance.

    Returns:
        MovieListResponseSchema: Serialized movie list item.
    """
    return MovieListResponseSchema(
        id=movie.id,
        uuid=movie.uuid,
        name=movie.name,
        year=movie.year,
        imdb=movie.imdb,
        price=float(movie.price),
        certification=movie.certification.name if movie.certification else None,
        genres=[g.name for g in movie.genres],
    )
