"""
Pydantic schemas for the movies module.

Defines request/response schemas for movies, genres, stars,
directors, certifications, comments, ratings, favorites, and likes.
"""

from pydantic import BaseModel, Field


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

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Star
# ──────────────────────────────────────────────

class StarCreateSchema(BaseModel):
    """Schema for creating a star/actor."""
    name: str = Field(..., min_length=1, max_length=255)


class StarResponseSchema(StarCreateSchema):
    """Schema for star response."""
    id: int

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Director
# ──────────────────────────────────────────────

class DirectorCreateSchema(BaseModel):
    """Schema for creating a director."""
    name: str = Field(..., min_length=1, max_length=255)


class DirectorResponseSchema(DirectorCreateSchema):
    """Schema for director response."""
    id: int

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Certification
# ──────────────────────────────────────────────

class CertificationResponseSchema(BaseModel):
    """Schema for certification response."""
    id: int
    name: str

    model_config = {"from_attributes": True}
