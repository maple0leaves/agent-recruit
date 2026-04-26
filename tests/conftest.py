"""
Phase 1 test fixtures.
Uses in-memory SQLite for isolated per-test database.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use in-memory SQLite for test isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# These will be imported once the backend modules exist in Plan 01-02.
# For now, define placeholder imports for test structure verification.
# After Plan 01-02 runs, uncomment the real imports:
# from backend.db.engine import engine, async_session, Base, get_session
# from backend.db.models.user import User, UserRole
# from backend.auth.password import hash_password
# from api.server import app

# --- Placeholder for Wave 0 ---
# The following fixtures will be properly wired after Plan 01-02 creates backend modules.
# For now, they provide the test structure skeleton.


@pytest_asyncio.fixture
async def test_engine():
    """Create an isolated in-memory SQLite engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create a clean async session for each test."""
    # Import Base and create tables
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(test_session):
    """Create an async HTTP client for testing API endpoints.

    After Plan 01-02, this should use the real FastAPI app:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    """
    transport = ASGITransport(app=None)  # Placeholder - will be replaced
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_session):
    """Create a seeded test user for auth tests.

    After Plan 01-02, this should:
    1. Create a User(username="testadmin", role=UserRole.ADMIN, hashed_password=hash_password("test1234"))
    2. Commit the user
    3. Return the user object
    """
    return {"username": "testadmin", "role": "admin"}
