"""
Read and normalize movie data from CSV.

Loads the raw dataset using pandas and converts each CSV row
into a normalized MovieSeed dataclass used by the database seeders.
"""
from decimal import Decimal
from pathlib import Path
from random import Random

import pandas as pd

from src.database.seeds.certifications import DEFAULT_CERTIFICATIONS
from src.database.seeds.models import MovieSeed


DATA_DIR = Path(__file__).parent / "data"
MOVIES_CSV = DATA_DIR / "movies.csv"

# Fixed seed so generated values are always identical.
RNG = Random(42)

# # Since the dataset does not contain certifications,
# assign one randomly from a realistic list.
# DEFAULT_CERTIFICATIONS = [
#     "G",
#     "PG",
#     "PG-13",
#     "R",
#     "NC-17",
#     "TV-G",
#     "TV-PG",
#     "TV-14",
#     "TV-MA",
#     "Approved",
#     "Passed",
#     "Unrated"
# ]

# Demo prices.
DEFAULT_PRICES = (
    4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 10.99, 11.99, 12.99, 13.99, 14.99
)

CHUNK_SIZE = 1000


def load_movies() -> list[MovieSeed]:
    """
    Read the CSV dataset and return normalized movie records.

    Returns:
        List of MovieSeed objects.
    """

    movies: list[MovieSeed] = []

    for chunk in pd.read_csv(
        MOVIES_CSV,
        chunksize=CHUNK_SIZE,
        keep_default_na=False
    ):
        for row in chunk.itertuples(index=False):
            movies.append(_build_movie_seed(row))

    return movies


def _build_movie_seed(row) -> MovieSeed:
    """
    Convert one CSV row into MovieSeed.

    Args:
        row:
            pandas namedtuple returned by DataFrame.itertuples().

    Returns:
        MovieSeed instance.
    """
    genres = [
        genre.strip() for genre in row.genre.split(",") if genre.strip()
    ]

    crew = [
        person.strip() for person in row.crew.split(",") if person.strip()
    ]

    # CSV does not distinguish directors.
    # Use the first person as a demo director.
    director = crew[0] if crew else "James Cameron"

    # Remaining people become actors.
    stars = crew[1:6]

    if not stars:
        stars = [director]

    # year = int(str(row.date_x)[:4])
    year = pd.to_datetime(row.date_x).year

    meta_score = float(row.score) if row.score != "" else None

    gross = float(row.revenue) if row.revenue != "" else None

    return MovieSeed(
        name=row.names,
        year=year,
        # Dataset has no duration.
        # Generate realistic demo duration.
        time=RNG.randint(80, 180),
        imdb=round(float(row.score) / 10, 1),
        votes=RNG.randint(5_000, 900_000),
        meta_score=meta_score,
        gross=gross,
        description=row.overview,
        certification=RNG.choice(DEFAULT_CERTIFICATIONS),
        genres=genres,
        director=director,
        stars=stars,
        price=Decimal(str(RNG.choice(DEFAULT_PRICES)))
    )
