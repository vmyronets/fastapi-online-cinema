"""
API routes for the movies module.

Provides endpoints for browsing movies, CRUD operations (moderator),
genres, comments, ratings, favorites, and likes/dislikes.
"""
import math
from typing import Optional, Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Depends,
)

from sqlalchemy import (
    select,
    func,
    or_
)
from sqlalchemy.ext.asyncio import AsyncSession

from security.dependencies import get_token, get_jwt_auth_manager
from security.exceptions import BaseSecurityError
from security.interfaces import JWTAuthManagerInterface
from src.database.session import get_db
from src.movies.models import (
    GenreModel,
    MovieModel,
    movie_genres
)
from movies.schemas import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    PaginatedResponseSchema,
    GenreResponseSchema,
    GenreCreateSchema,
)
from src.accounts.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum
)

router = APIRouter(prefix="/movies", tags=["Movies"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]

JWTManagerDep = Annotated[JWTAuthManagerInterface, Depends(get_jwt_auth_manager)]


# ----------------------------------------------
# Helpers
# ----------------------------------------------

def _decode_token(token: str, jwt_manager: JWTAuthManagerInterface) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT token string.
        jwt_manager: JWT manager instance for decoding.

    Returns:
        dict: The decoded token payload.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        return jwt_manager.decode_access_token(token)
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


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


def _build_movie_detail_response(
        movie: MovieModel
) -> MovieDetailResponseSchema:
    """
    Build a MovieDetailResponseSchema from a MovieModel instance.

    Args:
        movie: The MovieModel ORM instance.

    Returns:
        MovieDetailResponseSchema: Serialized movie detail.
    """
    return MovieDetailResponseSchema(
        id=movie.id,
        uuid=movie.uuid,
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=float(movie.price),
        certification=movie.certification.name if movie.certification else None,
        genres=[genre.name for genre in movie.genres],
        directors=[director.name for director in movie.directors],
        stars=[star.name for star in movie.stars]
    )


# ----------------------------------------------
# Movie Browsing (Public / Authenticated)
# ----------------------------------------------

@router.get(
    "/",
    response_model=PaginatedResponseSchema,
    summary="Browse movie catalog with pagination, "
            "filtering, sorting, and search"
)
async def list_movies(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(
        10, ge=1, le=100, description="Items per page"
    ),
    year: Optional[int] = Query(
        None, description="Filter by release year"
    ),
    min_imdb: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum IMDb rating"
    ),
    genre: Optional[str] = Query(
        None, description="Filter by genre name"
    ),
    sort_by: Optional[str] = Query(
        None, description="Sort field: price, year, imdb, name"
    ),
    sort_order: Optional[str] = Query(
        "asc", description="Sort order: asc or desc"
    ),
    search: Optional[str] = Query(
        None,
        description="Search by title, description, actor, or director"
    ),
) -> PaginatedResponseSchema:
    """
    Browse the movie catalog with pagination, filtering, sorting, and search.

    Steps:
    - Apply optional filters (year, min_imdb, genre).
    - Apply optional search across title, description, actors, directors.
    - Apply sorting by the specified field and order.
    - Return paginated results.

    Args:
        db (AsyncSession): The asynchronous database session.
        page (int): Page number (default 1).
        per_page (int): Items per page (default 10, max 100).
        year (int, optional): Filter by release year.
        min_imdb (float, optional): Minimum IMDb rating filter.
        genre (str, optional): Filter by genre name.
        sort_by (str, optional): Field to sort by.
        sort_order (str, optional): Sort direction (asc/desc).
        search (str, optional): Search query string.

    Returns:
        PaginatedResponseSchema: Paginated list of movies.
    """
    stmt = select(MovieModel)

    # Apply filters.
    if year:
        stmt = stmt.where(MovieModel.year == year)
    if min_imdb is not None:
        stmt = stmt.where(MovieModel.imdb >= min_imdb)
    if genre:
        stmt = stmt.join(MovieModel.genres).where(GenreModel.name == genre)

    # Apply search.
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                MovieModel.name.ilike(search_pattern),
                MovieModel.description.ilike(search_pattern),
            )
        )

    # Count total results.
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Apply sorting.
    sort_column = {
        "price": MovieModel.price,
        "year": MovieModel.year,
        "imdb": MovieModel.imdb,
        "name": MovieModel.name,
    }.get(sort_by, MovieModel.id)

    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Apply pagination.
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()

    return PaginatedResponseSchema(
        items=[_build_movie_list_response(m) for m in movies],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if per_page else 0,
    )


# ----------------------------------------------
# Genres (must be before /{movie_id}/ to avoid path conflicts)
# ----------------------------------------------

@router.get(
    "/genres/",
    response_model=list[GenreResponseSchema],
    summary="List all genres with movie counts",
)
async def list_genres(
    db: SessionDep,
) -> list[GenreResponseSchema]:
    """
    List all genres with the count of movies in each.

    Args:
        db (AsyncSession): The asynchronous database session.

    Returns:
        list[GenreResponseSchema]: List of genres with movie counts.
    """
    stmt = (
        select(
            GenreModel, func.count(
                movie_genres.c.movie_id).label("movie_count")
        )
        .outerjoin(movie_genres, GenreModel.id == movie_genres.c.genre_id)
        .group_by(GenreModel.id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        GenreResponseSchema(id=genre.id, name=genre.name, movie_count=count)
        for genre, count in rows
    ]


@router.post(
    "/genres/",
    response_model=GenreResponseSchema,
    summary="Create a genre (moderator)",
    status_code=status.HTTP_201_CREATED,
)
async def create_genre(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    data: GenreCreateSchema,
    token: str = Depends(get_token),
) -> GenreResponseSchema:
    """
    Create a new genre (moderator/admin only).

    Args:
        data (GenreCreateSchema): Genre data.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        db (AsyncSession): The asynchronous database session.

    Returns:
        GenreResponseSchema: The created genre.

    Raises:
        HTTPException: If not authorized or genre already exists.
    """
    payload = _decode_token(token, jwt_manager)
    await _require_moderator(db, payload.get("user_id"))

    genre = GenreModel(name=data.name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)

    return GenreResponseSchema(id=genre.id, name=genre.name, movie_count=0)
