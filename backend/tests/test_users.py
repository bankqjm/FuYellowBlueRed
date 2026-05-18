import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import User, Wallet, UserAddress
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_users.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def create_test_user(db, role="USER", phone="19900000001"):
    user = User(
        phone=phone,
        password_hash=hash_password("TestPass123"),
        nickname=f"测试{role}",
        role=role,
        status=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    wallet = Wallet(user_id=user.id, balance=1000.0, frozen_balance=0.0)
    db.add(wallet)
    await db.commit()
    return user


def auth_headers(user_id, role="USER"):
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_me(db, client):
    user = await create_test_user(db, role="USER", phone="19930000001")
    headers = auth_headers(user.id, role="USER")

    res = await client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == user.id
    assert data["phone"] == "19930000001"
    assert data["role"] == "USER"


@pytest.mark.asyncio
async def test_update_me(db, client):
    user = await create_test_user(db, role="USER", phone="19930000002")
    headers = auth_headers(user.id, role="USER")

    res = await client.put("/api/v1/users/me", json={
        "nickname": "新昵称",
        "avatar": "https://example.com/avatar.png",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["nickname"] == "新昵称"
    assert data["avatar"] == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_get_addresses(db, client):
    user = await create_test_user(db, role="USER", phone="19930000003")
    headers = auth_headers(user.id, role="USER")

    addr1 = UserAddress(
        user_id=user.id,
        contact_name="张三",
        contact_phone="13800000001",
        address="地址1",
        is_default=1,
    )
    addr2 = UserAddress(
        user_id=user.id,
        contact_name="李四",
        contact_phone="13800000002",
        address="地址2",
        is_default=0,
    )
    db.add_all([addr1, addr2])
    await db.commit()

    res = await client.get("/api/v1/users/addresses", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_address(db, client):
    user = await create_test_user(db, role="USER", phone="19930000004")
    headers = auth_headers(user.id, role="USER")

    res = await client.post("/api/v1/users/addresses", json={
        "contact_name": "王五",
        "contact_phone": "13900000001",
        "address": "新建地址100号",
        "latitude": 39.9,
        "longitude": 116.4,
        "is_default": 1,
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["contact_name"] == "王五"
    assert data["is_default"] == 1


@pytest.mark.asyncio
async def test_update_address(db, client):
    user = await create_test_user(db, role="USER", phone="19930000005")
    headers = auth_headers(user.id, role="USER")

    addr = UserAddress(
        user_id=user.id,
        contact_name="原姓名",
        contact_phone="13800000005",
        address="原地址",
        is_default=0,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)

    res = await client.put(f"/api/v1/users/addresses/{addr.id}", json={
        "contact_name": "新姓名",
        "address": "新地址200号",
        "is_default": 1,
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["contact_name"] == "新姓名"
    assert data["address"] == "新地址200号"
    assert data["is_default"] == 1


@pytest.mark.asyncio
async def test_delete_address(db, client):
    user = await create_test_user(db, role="USER", phone="19930000006")
    headers = auth_headers(user.id, role="USER")

    addr = UserAddress(
        user_id=user.id,
        contact_name="待删除",
        contact_phone="13800000006",
        address="待删除地址",
        is_default=0,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)

    res = await client.delete(f"/api/v1/users/addresses/{addr.id}", headers=headers)
    assert res.status_code == 200

    from sqlalchemy import select
    result = await db.execute(select(UserAddress).where(UserAddress.id == addr.id))
    assert result.scalar_one_or_none() is None
