"""Phase 1 test fixtures using file-based temp SQLite for isolation."""
import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from api.server import app
from backend.db.engine import Base
from backend.db.models.user import User, UserRole
from backend.auth.password import hash_password
from backend.api.deps import get_db


@pytest.fixture
def db_path():
    """Create a temporary SQLite database file for test isolation."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest_asyncio.fixture
async def test_engine(db_path):
    """Create an isolated SQLite engine for testing using a temp file."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create a clean async session for each test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(test_engine):
    """Create an async HTTP client with FastAPI dependency override for DB.

    Uses the test engine (file-based temp SQLite) so that data committed
    from test_user fixture is visible to the HTTP test client.
    """
    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def test_user(test_session):
    """Create a seeded test user for auth tests."""
    user = User(
        username="testadmin",
        hashed_password=hash_password("test1234"),
        role=UserRole.ADMIN,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user
