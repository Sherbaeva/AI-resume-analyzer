"""Test fixtures and app setup for pytest."""
import asyncio
import io
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.auth.jwt import create_access_token
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.repositories.permission_repo import PermissionRepository
from app.rbac.permissions import ALL_PERMISSIONS

# In-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///./test_ats.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── Auth fixtures ───────────────────────────────────────────

@pytest_asyncio.fixture
async def seeded_permissions(db_session):
    """Seed all permissions into test DB."""
    repo = PermissionRepository(db_session)
    await repo.seed(ALL_PERMISSIONS)
    await db_session.commit()


@pytest_asyncio.fixture
async def admin_user(db_session, seeded_permissions):
    repo = UserRepository(db_session)
    user = await repo.create(
        email="admin@test.local",
        password="testpassword",
        role=UserRole.admin,
    )
    await db_session.commit()
    return {"id": user.id, "email": "admin@test.local", "password": "testpassword", "role": "admin"}


@pytest_asyncio.fixture
async def hr_user(db_session, seeded_permissions):
    repo = UserRepository(db_session)
    user = await repo.create(
        email="hr@test.local",
        password="testpassword",
        role=UserRole.hr,
    )
    await db_session.commit()
    return {"id": user.id, "email": "hr@test.local", "password": "testpassword", "role": "hr"}


@pytest_asyncio.fixture
async def admin_token(admin_user):
    return create_access_token({"sub": str(admin_user["id"])})


@pytest_asyncio.fixture
async def hr_token(hr_user):
    return create_access_token({"sub": str(hr_user["id"])})


@pytest_asyncio.fixture
async def admin_client(client, admin_token):
    """AsyncClient with admin auth header pre-set."""
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client


@pytest_asyncio.fixture
async def hr_client(client, hr_token):
    """AsyncClient with hr auth header pre-set."""
    client.headers.update({"Authorization": f"Bearer {hr_token}"})
    return client


# ─── File fixtures ───────────────────────────────────────────

@pytest.fixture
def sample_txt_bytes() -> bytes:
    return b"John Doe\nSenior Python Developer\nSkills: FastAPI, PostgreSQL, Docker\n"


@pytest.fixture
def sample_txt_upload(sample_txt_bytes):
    return ("file", ("resume.txt", io.BytesIO(sample_txt_bytes), "text/plain"))
