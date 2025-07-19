"""
Pytest configuration and shared fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.db.session import get_db
from src.models.base import BaseModel
from src.models.user import User, UserRole
from src.core.security import security
from src.core.config import settings


# Override test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        phone_number="555-1234",
        department="Testing",
        hashed_password=security.get_password_hash("TestPassword123!"),
        role=UserRole.ESTIMATOR,
        is_active=True,
        is_verified=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_db) -> User:
    """Create a test admin user."""
    admin = User(
        username="testadmin",
        email="admin@example.com",
        full_name="Test Admin",
        phone_number="555-5678",
        department="Management",
        hashed_password=security.get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest.fixture
async def test_viewer(test_db) -> User:
    """Create a test viewer user."""
    viewer = User(
        username="testviewer",
        email="viewer@example.com",
        full_name="Test Viewer",
        phone_number="555-9999",
        department="Sales",
        hashed_password=security.get_password_hash("ViewerPassword123!"),
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True
    )
    test_db.add(viewer)
    await test_db.commit()
    await test_db.refresh(viewer)
    return viewer


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "TestPassword123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = await client.post(
        "/api/auth/login",
        data={
            "username": test_admin.username,
            "password": "AdminPassword123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}