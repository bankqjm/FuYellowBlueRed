import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['UPLOAD_DIR'] = '/tmp/test_uploads'

from app.main import app
from app.database import Base, get_db
from app.models.models import User, UserRole, UserStatus
from app.utils.auth import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        phone="13800138000",
        password_hash=hash_password("Test123456"),
        nickname="测试用户",
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_shop_owner(db_session):
    user = User(
        phone="13900139000",
        password_hash=hash_password("Test123456"),
        nickname="测试商家",
        role=UserRole.SHOP_OWNER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_rider(db_session):
    user = User(
        phone="13700137000",
        password_hash=hash_password("Test123456"),
        nickname="测试骑手",
        role=UserRole.RIDER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session):
    user = User(
        phone="13600136000",
        password_hash=hash_password("Test123456"),
        nickname="测试管理员",
        role=UserRole.ADMIN.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(client, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "phone": "13800138000",
        "password": "Test123456"
    })
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def admin_token(client, test_admin):
    response = await client.post("/api/v1/auth/login", json={
        "phone": "13600136000",
        "password": "Test123456"
    })
    return response.json()["data"]["access_token"]
