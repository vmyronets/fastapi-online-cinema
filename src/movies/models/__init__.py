"""
Movie ORM models.

Exports all movie-related SQLAlchemy models including movies,
genres, stars, directors, certifications, and association tables.
"""

from src.movies.models.genre import GenreModel
from src.movies.models.star import StarModel
from src.movies.models.director import DirectorModel
from src.movies.models.certification import CertificationModel
from src.movies.models.movie import MovieModel
from src.movies.models.associations import (
    movie_genres,
    movie_directors,
    movie_stars
)
from src.movies.models.favorite import FavoriteModel
from src.movies.models.rating import RatingModel
from src.movies.models.comment import CommentModel
from src.movies.models.movie_like import MovieLikeModel

__all__ = [
    "GenreModel",
    "StarModel",
    "DirectorModel",
    "CertificationModel",
    "MovieModel",
    "movie_genres",
    "movie_directors",
    "movie_stars",
    "FavoriteModel",
    "RatingModel",
    "CommentModel",
    "MovieLikeModel",
]
