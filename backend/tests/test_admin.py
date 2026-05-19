import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, ShopStatus, Order, OrderStatus, Wallet,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_admin.db"

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
async def test_approve_shop(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100001")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900100002")
    shop = Shop(
        user_id=owner.id,
        name="待审核店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.PENDING.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=3.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.put(f"/api/v1/admin/shop/{shop.id}/approve", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == ShopStatus.APPROVED.value


@pytest.mark.asyncio
async def test_approve_shop_non_admin(db, client):
    user = await create_test_user(db, role="USER", phone="19900100003")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900100004")
    shop = Shop(
        user_id=owner.id,
        name="待审核店铺2",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.PENDING.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=3.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    headers = auth_headers(user.id, role="USER")
    res = await client.put(f"/api/v1/admin/shop/{shop.id}/approve", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_reject_shop(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100005")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900100006")
    shop = Shop(
        user_id=owner.id,
        name="待审核店铺3",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.PENDING.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=3.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.put(f"/api/v1/admin/shop/{shop.id}/reject", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == ShopStatus.REJECTED.value


@pytest.mark.asyncio
async def test_list_pending_shops(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100007")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900100008")
    shop = Shop(
        user_id=owner.id,
        name="待审核店铺4",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.PENDING.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=3.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.get("/api/v1/admin/shop/pending", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert all(item["status"] == ShopStatus.PENDING.value for item in data["items"])


@pytest.mark.asyncio
async def test_list_users(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100009")
    await create_test_user(db, role="USER", phone="19900100010")
    await create_test_user(db, role="RIDER", phone="19900100011")

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 3

    res_keyword = await client.get("/api/v1/admin/users?keyword=19900100010", headers=headers)
    assert res_keyword.status_code == 200
    assert res_keyword.json()["data"]["total"] >= 1

    res_role = await client.get("/api/v1/admin/users?role=RIDER", headers=headers)
    assert res_role.status_code == 200
    assert all(item["role"] == "RIDER" for item in res_role.json()["data"]["items"])


@pytest.mark.asyncio
async def test_update_user_status(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100012")
    user = await create_test_user(db, role="USER", phone="19900100013")

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.put(
        f"/api/v1/admin/users/{user.id}/status?status=0",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == 0

    res_enable = await client.put(
        f"/api/v1/admin/users/{user.id}/status?status=1",
        headers=headers,
    )
    assert res_enable.status_code == 200
    assert res_enable.json()["data"]["status"] == 1


@pytest.mark.asyncio
async def test_get_platform_stats(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100014")

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.get("/api/v1/admin/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "user_count" in data
    assert "shop_count" in data
    assert "approved_shop_count" in data
    assert "order_count" in data
    assert "pending_order_count" in data


@pytest.mark.asyncio
async def test_get_platform_trend(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100015")

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.get("/api/v1/admin/stats/trend?days=7", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 7
    assert "date" in data[0]
    assert "orders" in data[0]
    assert "revenue" in data[0]
    assert "new_users" in data[0]


@pytest.mark.asyncio
async def test_list_all_orders(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900100016")
    user = await create_test_user(db, role="USER", phone="19900100017")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900100018")
    shop = Shop(
        user_id=owner.id,
        name="测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=3.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORDADMIN001",
        user_id=user.id,
        shop_id=shop.id,
        address="测试地址",
        phone="19900100017",
        total_amount=50.0,
        delivery_fee=3.0,
        status=OrderStatus.PENDING_PAYMENT.value,
    )
    db.add(order)
    await db.commit()

    headers = auth_headers(admin.id, role="ADMIN")
    res = await client.get("/api/v1/admin/orders", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
