"""
Dataclasses used during database seeding.

These models represent normalized CSV rows before they
are inserted into the database.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class RawMovieRow:
    name: str
    release_date: str
    score: float
    genre: str
    overview: str
    crew: str
    budget: float | None
    revenue: float | None
    country: str | None


@dataclass(slots=True)
class MovieSeed:
    """
    Normalized movie record loaded from CSV.
    """
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: str
    price: Decimal
    certification: str
    genres: list[str]
    director: str
    stars: list[str]
