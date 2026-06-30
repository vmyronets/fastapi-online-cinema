"""
API routes for the movies module.

Provides endpoints for browsing movies, CRUD operations (moderator),
genres, comments, ratings, favorites, and likes/dislikes.
"""
import math
from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Depends
)

from sqlalchemy import (
    select,
    func,
    or_
)
from sqlalchemy.ext.asyncio import AsyncSession

from movies.models import (
    CommentModel,
    RatingModel,
    MovieLikeModel
)
from src.accounts.routes import SessionDep, JWTManagerDep
from security.dependencies import get_token
from security.exceptions import BaseSecurityError
from security.interfaces import JWTAuthManagerInterface
from src.movies.models import (
    CertificationModel,
    DirectorModel,
    FavoriteModel,
    GenreModel,
    MovieModel,
    StarModel,
    movie_genres
)
from movies.schemas import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    PaginatedResponseSchema,
    GenreResponseSchema,
    GenreCreateSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    CommentResponseSchema,
    CommentCreateSchema,
    RatingResponseSchema,
    RatingCreateSchema,
    FavoriteResponseSchema,
    MovieLikeResponseSchema,
    MovieLikeCreateSchema
)
from src.accounts.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum
)

from src.orders.models import OrderItemModel

router = APIRouter(prefix="/movies", tags=["Movies"])


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


# ----------------------------------------------
# Favorites (must be before /{movie_id}/ to avoid path conflicts)
# ----------------------------------------------

@router.get(
    "/favorites/",
    response_model=PaginatedResponseSchema,
    summary="List user's favorite movies",
)
async def list_favorites(
        db: SessionDep,
        jwt_manager: JWTManagerDep,
        token: str = Depends(get_token),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
) -> PaginatedResponseSchema:
    """
    List the authenticated user's favorite movies with pagination.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.
        page (int): Page number.
        per_page (int): Items per page.

    Returns:
        PaginatedResponseSchema: Paginated list of favorite movies.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    stmt = (
        select(MovieModel)
        .join(FavoriteModel, FavoriteModel.movie_id == MovieModel.id)
        .where(FavoriteModel.user_id == user_id)
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

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


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    summary="Get movie details",
)
async def get_movie(
        movie_id: int,
        db: SessionDep,
) -> MovieDetailResponseSchema:
    """
    Get detailed information about a specific movie.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MovieDetailResponseSchema: Full movie details.

    Raises:
        HTTPException: If movie not found.
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found."
        )

    return _build_movie_detail_response(movie)


# ----------------------------------------------
# Movie CRUD (Moderator)
# ----------------------------------------------

@router.post(
    "/",
    response_model=MovieDetailResponseSchema,
    summary="Create a movie (moderator)",
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
        data: MovieCreateSchema,
        db: SessionDep,
        jwt_manager: JWTManagerDep,
        token: str = Depends(get_token),
) -> MovieDetailResponseSchema:
    """
    Create a new movie entry (moderator/admin only).

    Steps:
    - Verify moderator/admin privileges.
    - Validate certification exists.
    - Create movie with associated genres, directors, and stars.

    Args:
        data (MovieCreateSchema): Movie data.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        MovieDetailResponseSchema: The created movie details.

    Raises:
        HTTPException: If not authorized or certification not found.
    """
    payload = _decode_token(token, jwt_manager)
    await _require_moderator(db, payload.get("user_id"))

    # Verify certification exists.
    cert = (
        await db.execute(
            select(CertificationModel)
            .where(CertificationModel.id == data.certification_id)
        )
    ).scalars().first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certification not found."
        )

    movie = MovieModel(
        name=data.name,
        year=data.year,
        time=data.time,
        imdb=data.imdb,
        votes=data.votes,
        meta_score=data.meta_score,
        gross=data.gross,
        description=data.description,
        price=data.price,
        certification_id=data.certification_id,
    )

    # Attach genres.
    if data.genre_ids:
        genres = (
            await db.execute(
                select(GenreModel).where(GenreModel.id.in_(data.genre_ids)))
        ).scalars().all()
        movie.genres = list(genres)

    # Attach directors.
    if data.director_ids:
        directors = (
            await db.execute(
                select(DirectorModel).where(
                    DirectorModel.id.in_(data.director_ids)))
        ).scalars().all()
        movie.directors = list(directors)

    # Attach stars.
    if data.star_ids:
        stars = (
            await db.execute(
                select(StarModel).where(StarModel.id.in_(data.star_ids)))
        ).scalars().all()
        movie.stars = list(stars)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return _build_movie_detail_response(movie)


@router.patch(
    "/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    summary="Update a movie (moderator)",
)
async def update_movie(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    data: MovieUpdateSchema,
    token: str = Depends(get_token),
) -> MovieDetailResponseSchema:
    """
    Update an existing movie (moderator/admin only).

    Steps:
    - Verify moderator/admin privileges.
    - Find the movie.
    - Update only provided fields.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        data (MovieUpdateSchema): Fields to update.
        token (str): The authentication token.

    Returns:
        MovieDetailResponseSchema: The updated movie details.

    Raises:
        HTTPException: If not authorized or movie not found.
    """
    payload = _decode_token(token, jwt_manager)
    await _require_moderator(db, payload.get("user_id"))

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found."
        )

    # Update scalar fields.
    update_data = data.model_dump(exclude_unset=True)
    for field in (
            "name",
            "year",
            "time",
            "imdb",
            "votes",
            "meta_score",
            "gross",
            "description",
            "price",
            "certification_id"
    ):
        if field in update_data:
            setattr(movie, field, update_data[field])

    # Update relationships.
    if data.genre_ids is not None:
        genres = (
            await db.execute(
                select(GenreModel).where(GenreModel.id.in_(data.genre_ids)))
        ).scalars().all()
        movie.genres = list(genres)

    if data.director_ids is not None:
        directors = (
            await db.execute(select(DirectorModel).where(
                DirectorModel.id.in_(data.director_ids))
            )
        ).scalars().all()
        movie.directors = list(directors)

    if data.star_ids is not None:
        stars = (
            await db.execute(select(StarModel).where(
                StarModel.id.in_(data.star_ids))
            )
        ).scalars().all()
        movie.stars = list(stars)

    await db.commit()
    await db.refresh(movie)

    return _build_movie_detail_response(movie)


@router.delete(
    "/{movie_id}/",
    response_model=dict,
    summary="Delete a movie (moderator)",
)
async def delete_movie(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> dict:
    """
    Delete a movie (moderator/admin only).

    Prevents deletion if the movie has been purchased by any user.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If not authorized, movie not found, or movie has been purchased.
    """

    payload = _decode_token(token, jwt_manager)
    await _require_moderator(db, payload.get("user_id"))

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found."
        )

    # Check if movie has been purchased.
    purchase_check = (
        select(OrderItemModel)
        .where(OrderItemModel.movie_id == movie_id)
    )
    purchase_result = await db.execute(purchase_check)
    if purchase_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a movie that has been purchased.",
        )

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


# ----------------------------------------------
# Comments
# ----------------------------------------------

@router.post(
    "/{movie_id}/comments/",
    response_model=CommentResponseSchema,
    summary="Add a comment to a movie",
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    data: CommentCreateSchema,
    token: str = Depends(get_token),
) -> CommentResponseSchema:
    """
    Add a comment to a movie.

    Steps:
    - Authenticate user.
    - Verify movie exists.
    - Create comment (optionally as a reply to another comment).

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        data (CommentCreateSchema): Comment content and optional parent_id.
        token (str): The authentication token.

    Returns:
        CommentResponseSchema: The created comment.

    Raises:
        HTTPException: If not authenticated or movie not found.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    comment = CommentModel(
        user_id=user_id,
        movie_id=movie_id,
        content=data.content,
        parent_id=data.parent_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponseSchema(
        id=comment.id,
        user_id=comment.user_id,
        movie_id=comment.movie_id,
        content=comment.content,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
    )


@router.get(
    "/{movie_id}/comments/",
    response_model=list[CommentResponseSchema],
    summary="List comments for a movie",
)
async def list_comments(
    movie_id: int,
    db: SessionDep,
) -> list[CommentResponseSchema]:
    """
    List all comments for a specific movie.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.

    Returns:
        list[CommentResponseSchema]: List of comments.
    """
    stmt = (
        select(CommentModel)
        .where(CommentModel.movie_id == movie_id)
        .order_by(CommentModel.created_at)
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()

    return [
        CommentResponseSchema(
            id=comment.id,
            user_id=comment.user_id,
            movie_id=comment.movie_id,
            content=comment.content,
            parent_id=comment.parent_id,
            created_at=comment.created_at,
        )
        for comment in comments
    ]


# ----------------------------------------------
# Ratings
# ----------------------------------------------

@router.post(
    "/{movie_id}/ratings/",
    response_model=RatingResponseSchema,
    summary="Rate a movie",
    status_code=status.HTTP_201_CREATED,
)
async def rate_movie(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    data: RatingCreateSchema,
    token: str = Depends(get_token),
) -> RatingResponseSchema:
    """
    Rate a movie on a 1-10 scale.

    Creates or updates the user's rating for the movie.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        data (RatingCreateSchema): The rating score.
        token (str): The authentication token.

    Returns:
        RatingResponseSchema: The created/updated rating.

    Raises:
        HTTPException: If not authenticated.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    # Check for existing rating.
    stmt = select(RatingModel).where(
        RatingModel.user_id == user_id,
        RatingModel.movie_id == movie_id
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.score = data.score
        await db.commit()
        await db.refresh(existing)
        rating = existing
    else:
        rating = RatingModel(
            user_id=user_id,
            movie_id=movie_id,
            score=data.score
        )
        db.add(rating)
        await db.commit()
        await db.refresh(rating)

    return RatingResponseSchema(
        id=rating.id,
        user_id=rating.user_id,
        movie_id=rating.movie_id,
        score=rating.score,
        created_at=rating.created_at
    )


# ----------------------------------------------
# Favorites
# ----------------------------------------------

@router.post(
    "/{movie_id}/favorites/",
    response_model=FavoriteResponseSchema,
    summary="Add movie to favorites",
    status_code=status.HTTP_201_CREATED,
)
async def add_favorite(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> FavoriteResponseSchema:
    """
    Add a movie to the user's favorites.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        FavoriteResponseSchema: The created favorite entry.

    Raises:
        HTTPException: If already in favorites or not authenticated.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    # Check if already favorite.
    stmt = select(FavoriteModel).where(
        FavoriteModel.user_id == user_id,
        FavoriteModel.movie_id == movie_id
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in favorites."
        )

    fav = FavoriteModel(user_id=user_id, movie_id=movie_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)

    return FavoriteResponseSchema(
        id=fav.id,
        user_id=fav.user_id,
        movie_id=fav.movie_id,
        created_at=fav.created_at
    )


@router.delete(
    "/{movie_id}/favorites/",
    response_model=dict,
    summary="Remove movie from favorites",
)
async def remove_favorite(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> dict:
    """
    Remove a movie from the user's favorites.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If not in favorites or not authenticated.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    stmt = select(FavoriteModel).where(
        FavoriteModel.user_id == user_id,
        FavoriteModel.movie_id == movie_id
    )
    result = await db.execute(stmt)
    fav = result.scalars().first()
    if not fav:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in favorites."
        )

    await db.delete(fav)
    await db.commit()

    return {"detail": "Movie removed from favorites."}


# ----------------------------------------------
# Likes / Dislikes
# ----------------------------------------------

@router.post(
    "/{movie_id}/likes/",
    response_model=MovieLikeResponseSchema,
    summary="Like or dislike a movie",
    status_code=status.HTTP_201_CREATED,
)
async def like_movie(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    data: MovieLikeCreateSchema,
    token: str = Depends(get_token),
) -> MovieLikeResponseSchema:
    """
    Like or dislike a movie.

    Creates or updates the user's like/dislike for the movie.

    Args:
        movie_id (int): The movie's ID.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        data (MovieLikeCreateSchema): Whether it's a like (True) or dislike (False).
        token (str): The authentication token.

    Returns:
        MovieLikeResponseSchema: The created/updated like entry.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    stmt = select(MovieLikeModel).where(
        MovieLikeModel.user_id == user_id,
        MovieLikeModel.movie_id == movie_id
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.is_like = data.is_like
        await db.commit()
        await db.refresh(existing)
        like = existing
    else:
        like = MovieLikeModel(
            user_id=user_id,
            movie_id=movie_id,
            is_like=data.is_like
        )
        db.add(like)
        await db.commit()
        await db.refresh(like)

    return MovieLikeResponseSchema(
        id=like.id,
        user_id=like.user_id,
        movie_id=like.movie_id,
        is_like=like.is_like,
        created_at=like.created_at
    )
