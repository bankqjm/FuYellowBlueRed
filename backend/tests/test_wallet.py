import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import User, Wallet, FundFlow
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_wallet.db"

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
async def test_get_wallet(db, client):
    user = await create_test_user(db, role="USER", phone="19940000001")
    headers = auth_headers(user.id, role="USER")

    res = await client.get("/api/v1/wallet", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["balance"] == 1000.0
    assert data["frozen_balance"] == 0.0
    assert "total_income" in data
    assert "total_expense" in data


@pytest.mark.asyncio
async def test_recharge_wallet_admin(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19940000002")
    user = await create_test_user(db, role="USER", phone="19940000021")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.post(f"/api/v1/wallet/recharge/{user.id}?amount=500.0", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["amount"] == 500.0


@pytest.mark.asyncio
async def test_recharge_wallet_non_admin(db, client):
    user = await create_test_user(db, role="USER", phone="19940000003")
    headers = auth_headers(user.id, role="USER")

    res = await client.post("/api/v1/wallet/recharge/1?amount=100.0", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_recharge_user_wallet(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19940000004")
    user = await create_test_user(db, role="USER", phone="19940000005")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.post(f"/api/v1/wallet/recharge/{user.id}?amount=200.0", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user_id"] == user.id
    assert data["amount"] == 200.0
    assert data["balance"] == 1200.0


@pytest.mark.asyncio
async def test_get_transactions(db, client):
    user = await create_test_user(db, role="USER", phone="19940000006")
    headers = auth_headers(user.id, role="USER")

    fund_flow = FundFlow(
        user_id=user.id,
        account_type="USER",
        flow_type="INCOME",
        amount=100.0,
        balance_before=0.0,
        balance_after=100.0,
        business_type="RECHARGE",
        description="测试充值",
    )
    db.add(fund_flow)
    await db.commit()

    res = await client.get("/api/v1/wallet/transactions", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["flow_type"] == "INCOME"
    assert data["items"][0]["amount"] == 100.0
