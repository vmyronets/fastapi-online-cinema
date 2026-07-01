"""
Query filters and modifiers for the movies module.
"""
import math
from typing import Optional, Callable, Any
from sqlalchemy import Select, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.movies.models import (
    MovieModel,
    GenreModel,
    StarModel,
    DirectorModel
)
from movies.schemas import PaginatedResponseSchema


def apply_movie_filters_and_sort(
    stmt: Select,
    year: Optional[int] = None,
    min_imdb: Optional[float] = None,
    genre: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc"
) -> Select:
    """
    Applies filtering, searching, and sorting to a base Movie query.

    Args:
        stmt (Select): The base SQLAlchemy select statement.
        year (int, optional): Filter by release year.
        min_imdb (float, optional): Minimum IMDb rating.
        genre (str, optional): Filter by genre name.
        search (str, optional): Search by title, description, actor, or director.
        sort_by (str, optional): Field to sort by.
        sort_order (str, optional): Sort direction ('asc' or 'desc').

    Returns:
        Select: The modified SQLAlchemy statement.
    """
    # 1. Apply filters.
    if year:
        stmt = stmt.where(MovieModel.year == year)
    if min_imdb is not None:
        stmt = stmt.where(MovieModel.imdb >= min_imdb)
    if genre:
        stmt = stmt.join(MovieModel.genres).where(GenreModel.name == genre)

    # 2. Apply search.
    if search:
        search_pattern = f"%{search}%"
        stmt = (
            stmt.outerjoin(MovieModel.stars)
            .outerjoin(MovieModel.directors)
            .where(
                or_(
                    MovieModel.name.ilike(search_pattern),
                    MovieModel.description.ilike(search_pattern),
                    StarModel.name.ilike(search_pattern),
                    DirectorModel.name.ilike(search_pattern)
                )
            )
        )

    # 3. Apply sorting.
    sort_column = {
        "price": MovieModel.price,
        "year": MovieModel.year,
        "imdb": MovieModel.imdb,
        "name": MovieModel.name,
        "popularity": MovieModel.votes
    }.get(sort_by, MovieModel.id)

    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    return stmt


async def get_paginated_response(
    db: AsyncSession,
    stmt: Select,
    page: int,
    per_page: int,
    transform_item: Callable[[Any], Any]
) -> PaginatedResponseSchema:
    """
    A versatile helper for counting items, implementing
    pagination, and generating a PaginatedResponseSchema.

    Args:
        db (AsyncSession): Asynchronous Database Session.
        stmt (Select): The SQLAlchemy query that has been constructed (already with filters and sorting).
        page (int): Page number.
        per_page (int): Number of elements on the page.
        transform_item (Callable): A function for converting an ORM model into a response schema.
    """
    # Counting the total number of results using a subquery
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Applying Offset and Limit
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    raw_items = result.scalars().unique().all()

    # Convert ORM objects to the desired schema format
    transformed_items = [transform_item(item) for item in raw_items]

    # Returning the completed pagination scheme
    return PaginatedResponseSchema(
        items=transformed_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if per_page else 0
    )
