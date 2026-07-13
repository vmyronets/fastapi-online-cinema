"""
Shared test fixtures for the FastAPI Online Cinema test suite.

Configures an async SQLite database for testing, overrides FastAPI
dependencies, and provides reusable fixtures for authenticated users,
movies, carts, orders, and JWT tokens.
"""

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID

from src.movies.models import CertificationModel, MovieModel
from src.accounts.models import (
    UserModel,
    UserGroupEnum,
    UserGroupModel
)
from src.database.session import Base, get_db
from src.notifications.emails import get_email_sender
from src.notifications.interfaces import EmailSenderInterface
from src.security.dependencies import get_s3_storage_client
from src.security.interfaces import S3StorageInterface
from src.security.jwt_manager import JWTAuthManager
from src.security.password import hash_password
from src.main import app


# ---------------------------------------------------------------------------
# SQLite-compatible type overrides
# ---------------------------------------------------------------------------
@compiles(UUID, "sqlite")
def compile_uuid_as_string_for_sqlite(_type, _compiler, **_kw):
    """
    Automatically converts any PostgreSQL UUID to a String(36)
    when generating schemas for SQLite in tests.
    """
    return "VARCHAR(36)"


# ---------------------------------------------------------------------------
# Async SQLite engine & session for tests
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Mock S3 client (no real S3 in tests)
# ---------------------------------------------------------------------------
class MockS3StorageClient(S3StorageInterface):
    """In-memory mock for S3 storage operations."""

    async def upload_file(self, file_name: str, file_data: bytes) -> None:
        ...

    async def get_file_url(self, file_name: str) -> str:
        return f"http://mock-s3/{file_name}"


# ---------------------------------------------------------------------------
# Mock email sender (no real email sending in tests)
# ---------------------------------------------------------------------------
class MockEmailSender(EmailSenderInterface):
    """Mock email sender for tests."""

    async def send_activation_email(
        self,
        email: str,
        activation_link: str
    ) -> None:
        return None

    async def send_activation_complete_email(
        self,
        email: str,
        login_link: str
    ) -> None:
        return None

    async def send_password_reset_email(
        self,
        email: str,
        reset_link: str
    ) -> None:
        return None

    async def send_password_reset_complete_email(
        self,
        email: str,
        login_link: str
    ) -> None:
        return None

    async def send_comment_reply_email(
        self,
        email: str,
        movie_title: str,
        replier_name: str,
        comment_content: str
    ) -> None:
        return None

    async def send_comment_like_email(
        self,
        email: str,
        movie_title: str,
        comment_preview: str
    ) -> None:
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    # Import all models so metadata is populated.
    import src.accounts.models  # noqa: F401
    import src.movies.models  # noqa: F401
    import src.cart.models  # noqa: F401
    import src.orders.models  # noqa: F401
    import src.payments.models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a fresh async database session for a test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provide an async HTTP test client with overridden dependencies."""

    async def _override_get_db():
        yield db_session

    def _override_s3():
        return MockS3StorageClient()

    def _override_email_sender():
        return MockEmailSender()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_s3_storage_client] = _override_s3
    app.dependency_overrides[get_email_sender] = _override_email_sender

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def jwt_manager() -> JWTAuthManager:
    """Provide a real JWT manager instance for token operations."""
    return JWTAuthManager()


# ---------------------------------------------------------------------------
# Helper: seed user groups
# ---------------------------------------------------------------------------
async def _seed_groups(session: AsyncSession):
    """Insert the three default user groups if they don't exist."""

    result = await session.execute(select(UserGroupModel))
    if result.scalars().first() is None:
        for grp in UserGroupEnum:
            session.add(UserGroupModel(name=grp.value))
        await session.commit()


# ---------------------------------------------------------------------------
# Helper: create a user the database and return
# ---------------------------------------------------------------------------
async def create_test_user(
    session: AsyncSession,
    email: str = "test@example.com",
    password: str = "TestPass1!",
    is_active: bool = True,
    group_name: UserGroupEnum = UserGroupEnum.USER
) -> UserModel:
    """Create a test user in the database and return the UserModel."""

    await _seed_groups(session)

    result = await session.execute(
        select(UserGroupModel).where(UserGroupModel.name == group_name)
    )
    group = result.scalars().first()

    if group is None:
        raise ValueError(f"User group {group_name.value} not found")

    user = UserModel(
        email=email,
        hashed_password=hash_password(password),
        is_active=is_active,
        group_id=group.id
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


# ---------------------------------------------------------------------------
# Helper: log in a user and return access and refresh tokens
# ---------------------------------------------------------------------------
async def login_test_user(
        client: AsyncClient,
        email: str = "test@example.com",
        password: str = "TestPass1!"
) -> dict:
    """
    Log in user and return access and refresh tokens as dict.
    """
    response = await client.post(
        "/api/v1/accounts/login/",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text

    return response.json()


# ---------------------------------------------------------------------------
# Helper: create a movie
# ---------------------------------------------------------------------------
async def create_test_movie(
    session: AsyncSession,
    name: str = "Test Movie",
    year: int = 2024,
    time: int = 120,
    price: Decimal = Decimal("9.99")
) -> "MovieModel":
    """Create a movie with a certification and return the MovieModel."""

    result = await session.execute(
        select(CertificationModel).where(CertificationModel.name == "PG-13")
    )
    cert = result.scalars().first()
    if cert is None:
        cert = CertificationModel(name="PG-13")
        session.add(cert)
        await session.commit()
        await session.refresh(cert)

    movie = MovieModel(
        uuid=uuid.uuid4(),
        name=name,
        year=year,
        time=time,
        imdb=8.0,
        votes=1000,
        description="A test movie.",
        price=price,
        certification_id=cert.id
    )
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    return movie
