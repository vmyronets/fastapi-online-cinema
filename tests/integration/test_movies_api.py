from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_movie


class TestMovieList:
    """Tests for movie listing endpoint."""

    async def test_list_movies_empty(self, client: AsyncClient) -> None:
        """
        Tests that the movie listing endpoint returns
        an empty list when no movies are present.
        """
        resp = await client.get("/api/v1/movies/")
        assert len(resp.json()["items"]) == 0
        assert isinstance(resp.json()["items"], list)
        assert resp.status_code == 200

    async def test_list_movies_with_data(
            self,
            client: AsyncClient,
            db_session: AsyncSession) -> None:
        """
        Tests that the movie listing endpoint returns
        a list of movies when movies are present.
        """
        await create_test_movie(db_session, name="Movie A")
        await create_test_movie(db_session, name="Movie B", year=2023, time=90)
        resp = await client.get("/api/v1/movies/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2


class TestMovieDetail:
    """Tests for movie detail endpoint."""

    async def test_get_detailed_movie(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that the movie detail endpoint returns a movie."""
        movie = await create_test_movie(db_session)
        resp = await client.get(f"/api/v1/movies/{movie.id}/")
        assert resp.status_code == 200

    async def test_get_nonexistent_movie(self, client: AsyncClient) -> None:
        """
        Tests that the movie detail endpoint
        returns a 404 for a nonexistent movie.
        """
        resp = await client.get("/api/v1/movies/99999/")
        assert resp.status_code == 404


class TestGenres:
    """Tests for genre endpoints."""

    async def test_list_genres(self, client: AsyncClient) -> None:
        """Tests that the genre listing endpoint returns a list of genres."""
        resp = await client.get("/api/v1/movies/genres/")
        assert resp.status_code == 200
