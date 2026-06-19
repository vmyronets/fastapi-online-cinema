"""
Pydantic schemas for the movies module.

Defines request/response schemas for movies, genres, stars,
directors, certifications, comments, ratings, favorites, and likes.
"""

from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


# ──────────────────────────────────────────────
# Genre
# ──────────────────────────────────────────────

class GenreCreateSchema(BaseModel):
    """Schema for creating a genre."""
    name: str = Field(..., min_length=1, max_length=100)


class GenreResponseSchema(GenreCreateSchema):
    """Schema for genre response with movie count."""
    id: int
    movie_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Star
# ──────────────────────────────────────────────

class StarCreateSchema(BaseModel):
    """Schema for creating a star/actor."""
    name: str = Field(..., min_length=1, max_length=255)


class StarResponseSchema(StarCreateSchema):
    """Schema for star response."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Director
# ──────────────────────────────────────────────

class DirectorCreateSchema(BaseModel):
    """Schema for creating a director."""
    name: str = Field(..., min_length=1, max_length=255)


class DirectorResponseSchema(DirectorCreateSchema):
    """Schema for director response."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Certification
# ──────────────────────────────────────────────

class CertificationResponseSchema(BaseModel):
    """Schema for certification response."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Movie
# ──────────────────────────────────────────────

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
    price: float = Field(..., ge=0)
    certification_id: int
    genre_ids: list[int] = []
    director_ids: list[int] = []
    star_ids: list[int] = []


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
