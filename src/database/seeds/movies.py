"""
Seed movies and all related entities.

Loads the normalized movie dataset, ensures that all related
entities exist in the database, then creates movies together
with many-to-many relationships.
"""

from collections.abc import Iterable
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.seeds.dataset import load_movies
from src.database.seeds.helpers import insert_if_not_exists
from src.database.seeds.models import MovieSeed

from src.movies.models.certification import CertificationModel
from src.movies.models.director import DirectorModel
from src.movies.models.genre import GenreModel
from src.movies.models.movie import MovieModel
from src.movies.models.star import StarModel


logger = logging.getLogger(__name__)


async def seed_movies(session: AsyncSession) -> None:
    """
    Seed movies together with related entities.

    Args:
        session: AsyncSession

    Steps:
        - Load CSV dataset.
        - Create any missing lookup entities.
        - Build lookup dictionaries.
        - Create MovieModel objects.
        - Create many-to-many relationships.
    """

    logger.info("Loading movie dataset...")

    movies = load_movies()

    logger.info("Loaded %s movies.", len(movies))

    await _seed_missing_entities(session, movies)

    certifications = await _build_lookup(session, CertificationModel)
    genres = await _build_lookup(session, GenreModel)
    directors = await _build_lookup(session, DirectorModel)
    stars = await _build_lookup(session, StarModel)

    logger.info("Creating movie records...")

    movie_lookup = await _create_movies(
        session=session,
        movies=movies,
        certifications=certifications
    )

    await _create_relationships(
        session=session,
        movies=movies,
        movie_lookup=movie_lookup,
        genres=genres,
        directors=directors,
        stars=stars
    )

    await session.flush()

    logger.info("Movie seeding finished.")


async def _build_lookup(
    session: AsyncSession,
    model: type
) -> dict[str, type]:
    """
    Load all rows of the given model and build a lookup
    dictionary keyed by the 'name' column.

    Example:

        {
            "Action": GenreModel(...),
            "Drama": GenreModel(...)
        }
    """

    result = await session.execute(select(model))

    return {
        row.name: row for row in result.scalars()
    }


async def _seed_missing_entities(
    session: AsyncSession,
    movies: list[MovieSeed]
) -> None:
    """
    Insert all missing genres, directors,
    stars and certifications.
    """

    await insert_if_not_exists(
        session=session,
        model=GenreModel,
        values=[
            {"name": name} for name in _collect_genres(movies)
        ]
    )

    await insert_if_not_exists(
        session=session,
        model=CertificationModel,
        values=[
            {"name": name} for name in _collect_certifications(movies)
        ]
    )

    await insert_if_not_exists(
        session=session,
        model=DirectorModel,
        values=[
            {"name": name} for name in _collect_directors(movies)
        ]
    )

    await insert_if_not_exists(
        session=session,
        model=StarModel,
        values=[
            {"name": name} for name in _collect_stars(movies)
        ]
    )

    await session.flush()


def _collect_genres(
    movies: Iterable[MovieSeed],
) -> list[str]:
    """
    Collect unique genre names.
    """

    return sorted(
        {genre for movie in movies for genre in movie.genres}
    )


def _collect_certifications(
    movies: Iterable[MovieSeed],
) -> list[str]:
    """
    Collect unique certification names.
    """

    return sorted(
        {movie.certification for movie in movies}
    )


def _collect_directors(
    movies: Iterable[MovieSeed]
) -> list[str]:
    """
    Collect unique director names.
    """

    return sorted(
        {movie.director for movie in movies}
    )


def _collect_stars(
    movies: Iterable[MovieSeed]
) -> list[str]:

    """
    Collect unique actor names.
    """
    return sorted(
        {star for movie in movies for star in movie.stars}
    )


async def _create_movies(
    session: AsyncSession,
    movies: list[MovieSeed],
    certifications: dict[str, CertificationModel]
) -> dict[tuple[str, int, int], MovieModel]:
    """
    Create movie records.

    Movies are inserted only once and then loaded into a lookup
    dictionary for relationship creation.

    Args:
        session: Active database session.
        movies: Normalized dataset.
        certifications: Certification lookup by name.

    Returns:
        Dictionary keyed by (name, year, duration).
    """

    values = [
        {
            "name": movie.name,
            "year": movie.year,
            "time": movie.time,
            "imdb": movie.imdb,
            "votes": movie.votes,
            "meta_score": movie.meta_score,
            "gross": movie.gross,
            "description": movie.description,
            "price": movie.price,
            "certification_id": certifications[movie.certification].id
        }
        for movie in movies
    ]

    await insert_if_not_exists(
        session=session,
        model=MovieModel,
        values=values,
        conflict_columns=[
            "name",
            "year",
            "time"
        ]
    )
    await session.flush()

    result = await session.execute(select(MovieModel))

    return {
        (movie.name, movie.year, movie.time): movie
        for movie in result.scalars()
    }


async def _create_relationships(
    session: AsyncSession,
    movies: list[MovieSeed],
    movie_lookup: dict[tuple[str, int, int], MovieModel],
    genres: dict[str, GenreModel],
    directors: dict[str, DirectorModel],
    stars: dict[str, StarModel]
) -> None:
    """
    Populate many-to-many relationships for movies.

    Relationships are created after all MovieModel objects
    already exist in the database.

    Args:
        session: Active SQLAlchemy session.
        movies: Normalized movie dataset.
        movie_lookup: Dictionary containing created MovieModel objects.
        genres: Genre lookup.
        directors: Director lookup.
        stars: Star lookup.
    """

    for movie in movies:
        db_movie = movie_lookup[
            (
                movie.name, movie.year, movie.time
            )
        ]

        # Genres
        existing_genres = {genre.name for genre in db_movie.genres}

        for genre in movie.genres:
            if genre in genres and genre not in existing_genres:
                db_movie.genres.append(genres[genre])
                existing_genres.add(genre)

        # Directors
        existing_directors = {director.name for director in db_movie.directors}
        if (
                movie.director in directors
                and movie.director not in existing_directors
        ):
            db_movie.directors.append(directors[movie.director])
            existing_directors.add(movie.director)

        # Stars
        existing_stars = {star.name for star in db_movie.stars}
        for star in movie.stars:
            if star in stars and star not in existing_stars:
                db_movie.stars.append(stars[star])
                existing_stars.add(star)

    await session.flush()
