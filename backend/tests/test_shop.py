import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, Product, Category, Order, OrderStatus,
    ShopStatus, ProductStatus, Wallet,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_shop.db"

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
async def test_apply_shop(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000001")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    res = await client.post("/api/v1/shop/apply", json={
        "name": "测试店铺",
        "address": "测试地址123号",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "测试店铺"
    assert data["status"] == ShopStatus.PENDING.value


@pytest.mark.asyncio
async def test_apply_shop_duplicate(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000002")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    await client.post("/api/v1/shop/apply", json={
        "name": "测试店铺",
        "address": "测试地址123号",
    }, headers=headers)

    res = await client.post("/api/v1/shop/apply", json={
        "name": "另一个店铺",
        "address": "另一个地址456号",
    }, headers=headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_get_my_shop(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000003")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="我的店铺",
        address="测试地址789号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()

    res = await client.get("/api/v1/shop/my", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "我的店铺"


@pytest.mark.asyncio
async def test_update_my_shop(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000004")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="原店铺名",
        address="原地址100号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()

    res = await client.put("/api/v1/shop/my", json={
        "name": "新店铺名",
        "notice": "新公告",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "新店铺名"


@pytest.mark.asyncio
async def test_create_product(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000005")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="商品店铺",
        address="商品地址200号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="热菜", sort_order=1)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    res = await client.post("/api/v1/shop/product", json={
        "shop_id": shop.id,
        "name": "宫保鸡丁",
        "price": 28.0,
        "stock": 50,
        "category_id": category.id,
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "宫保鸡丁"
    assert data["price"] == 28.0


@pytest.mark.asyncio
async def test_update_product(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000006")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="更新商品店铺",
        address="更新地址300号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    product = Product(
        shop_id=shop.id,
        name="原商品",
        price=20.0,
        stock=10,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    res = await client.put(f"/api/v1/shop/product/{product.id}", json={
        "name": "新商品",
        "price": 35.0,
        "stock": 20,
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "新商品"
    assert data["price"] == 35.0


@pytest.mark.asyncio
async def test_delete_product(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000007")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="删除商品店铺",
        address="删除地址400号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    product = Product(
        shop_id=shop.id,
        name="待删除商品",
        price=15.0,
        stock=5,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    res = await client.delete(f"/api/v1/shop/product/{product.id}", headers=headers)
    assert res.status_code == 200

    from sqlalchemy import select
    result = await db.execute(select(Product).where(Product.id == product.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_accept_order(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000008")
    user = await create_test_user(db, role="USER", phone="19910000009")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="接单店铺",
        address="接单地址500号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD001",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000001",
        total_amount=50.0,
        status=OrderStatus.PENDING_ACCEPT,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    res = await client.put(f"/api/v1/shop/my/orders/{order.id}/accept", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == OrderStatus.ACCEPTED.value


@pytest.mark.asyncio
async def test_reject_order_refunds(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000010")
    user = await create_test_user(db, role="USER", phone="19910000011")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="拒单店铺",
        address="拒单地址600号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD002",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000002",
        total_amount=80.0,
        status=OrderStatus.PENDING_ACCEPT,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    from app.models.models import PaymentTransaction
    from datetime import datetime
    payment = PaymentTransaction(
        order_id=order.id,
        user_id=user.id,
        trade_no="TR001",
        trade_type="PAY",
        amount=80.0,
        channel="BALANCE",
        status="SUCCESS",
        completed_at=datetime.now(),
    )
    db.add(payment)
    await db.commit()

    original_balance = (await db.execute(
        __import__("sqlalchemy").select(Wallet).where(Wallet.user_id == user.id)
    )).scalar_one().balance

    res = await client.put(
        f"/api/v1/shop/my/orders/{order.id}/reject",
        json={"reason": "无法制作"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == OrderStatus.CANCELLED.value

    from sqlalchemy import select
    updated_wallet = (await db.execute(
        select(Wallet).where(Wallet.user_id == user.id)
    )).scalar_one()
    assert updated_wallet.balance == original_balance + 80.0


@pytest.mark.asyncio
async def test_order_ready(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000012")
    user = await create_test_user(db, role="USER", phone="19910000013")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="备餐店铺",
        address="备餐地址700号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD003",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000003",
        total_amount=60.0,
        status=OrderStatus.ACCEPTED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    res = await client.put(f"/api/v1/shop/my/orders/{order.id}/ready", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == OrderStatus.READY.value


@pytest.mark.asyncio
async def test_get_shop_stats(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000014")
    user = await create_test_user(db, role="USER", phone="19910000015")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="统计店铺",
        address="统计地址800号",
        status=ShopStatus.APPROVED.value,
        rating=4.8,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order1 = Order(
        order_no="ORD010",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000010",
        total_amount=100.0,
        status=OrderStatus.COMPLETED,
    )
    order2 = Order(
        order_no="ORD011",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000010",
        total_amount=50.0,
        status=OrderStatus.PENDING_ACCEPT,
    )
    db.add_all([order1, order2])
    await db.commit()

    res = await client.get("/api/v1/shop/my/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_orders"] >= 2
    assert data["total_revenue"] >= 100.0
    assert data["pending_orders"] >= 1
    assert data["rating"] == 4.8


@pytest.mark.asyncio
async def test_get_shop_trend(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19910000016")
    user = await create_test_user(db, role="USER", phone="19910000017")
    headers = auth_headers(owner.id, role="SHOP_OWNER")

    shop = Shop(
        user_id=owner.id,
        name="趋势店铺",
        address="趋势地址900号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD020",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000020",
        total_amount=200.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()

    res = await client.get("/api/v1/shop/my/stats/trend?days=7", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert isinstance(data, list)
    assert len(data) == 7
    assert "date" in data[0]
    assert "orders" in data[0]
    assert "revenue" in data[0]
