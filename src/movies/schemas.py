"""
Pydantic schemas for the movies module.

Defines request/response schemas for movies, genres, stars,
directors, certifications, comments, ratings, favorites, and likes.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


# ----------------------------------------------
# Genre
# ----------------------------------------------

class GenreCreateSchema(BaseModel):
    """Schema for creating a genre."""
    name: str = Field(..., min_length=1, max_length=100)


class GenreResponseSchema(GenreCreateSchema):
    """Schema for genre response with movie count."""
    id: int
    movie_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Star
# ----------------------------------------------

class StarCreateSchema(BaseModel):
    """Schema for creating a star/actor."""
    name: str = Field(..., min_length=1, max_length=255)


class StarResponseSchema(StarCreateSchema):
    """Schema for star response."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Director
# ----------------------------------------------

class DirectorCreateSchema(BaseModel):
    """Schema for creating a director."""
    name: str = Field(..., min_length=1, max_length=255)


class DirectorResponseSchema(DirectorCreateSchema):
    """Schema for director response."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Certification
# ----------------------------------------------

class CertificationResponseSchema(BaseModel):
    """Schema for certification response."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Movie
# ----------------------------------------------

class MovieCreateSchema(BaseModel):
    """
    Schema for creating a movie.

    Attributes:
        name: Movie title.
        year: Release year.
        time: Duration in minutes.
        imdb: IMDb rating.
        votes: Number of IMDb votes.
        meta_score: Metascore (optional).
        gross: Gross revenue (optional).
        description: Movie synopsis.
        price: Movie price.
        certification_id: Foreign key to certification.
        genre_ids: List of genre IDs.
        director_ids: List of director IDs.
        star_ids: List of star IDs.
    """
    name: str = Field(..., min_length=1, max_length=255)
    year: int
    time: int
    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal = Field(..., ge=0)
    certification_id: int
    genre_ids: list[int] = Field(default_factory=list)
    director_ids: list[int] = Field(default_factory=list)
    star_ids: list[int] = Field(default_factory=list)


class MovieUpdateSchema(BaseModel):
    """Schema for updating a movie. All fields optional."""
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    certification_id: Optional[int] = None
    genre_ids: Optional[list[int]] = None
    director_ids: Optional[list[int]] = None
    star_ids: Optional[list[int]] = None


class MovieListResponseSchema(BaseModel):
    """
    Schema for movie list response (paginated).

    Attributes:
        id: Movie ID.
        uuid: Movie UUID.
        name: Movie title.
        year: Release year.
        imdb: IMDb rating.
        price: Movie price.
        certification: Certification name.
        genres: List of genre names.
    """
    id: int
    uuid: UUID
    name: str
    year: int
    imdb: float
    price: Decimal = Field(..., ge=0)
    certification: Optional[str] = None
    genres: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseSchema(MovieListResponseSchema):
    """
    Schema for detailed movie response.

    Includes all movie attributes plus related entities.
    """

    time: int
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    directors: list[str] = Field(default_factory=list)
    stars: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Comment
# ----------------------------------------------

class CommentCreateSchema(BaseModel):
    """Schema for creating a comment on a movie."""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = None


class CommentResponseSchema(CommentCreateSchema):
    """Schema for comment response."""
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Rating
# ----------------------------------------------

class RatingCreateSchema(BaseModel):
    """Schema for rating a movie (1-10 scale)."""
    score: float = Field(..., ge=1, le=10)


class RatingResponseSchema(RatingCreateSchema):
    """Schema for rating response."""
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Favorite
# ----------------------------------------------

class FavoriteResponseSchema(BaseModel):
    """Schema for favorite movie response."""
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Like / Dislike
# ----------------------------------------------

class MovieLikeCreateSchema(BaseModel):
    """Schema for liking/disliking a movie."""
    is_like: bool


class MovieLikeResponseSchema(MovieLikeCreateSchema):
    """Schema for movie like response."""
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------
# Pagination
# ----------------------------------------------

class PaginatedResponseSchema(BaseModel):
    """
    Generic paginated response wrapper.

    Attributes:
        items: List of items for the current page.
        total: Total number of items.
        page: Current page number.
        per_page: Items per page.
        pages: Total number of pages.
    """
    items: list
    total: int
    page: int
    per_page: int
    pages: int
