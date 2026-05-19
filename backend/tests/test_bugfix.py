import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import User, Shop, Product, Wallet, UserAddress
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_bugfix.db"

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


async def create_test_user(db, role="USER", phone="13800000001"):
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


async def create_test_address(db, user_id):
    addr = UserAddress(
        user_id=user_id,
        contact_name="测试收货人",
        contact_phone="13900000000",
        address="测试地址123号",
        latitude=39.9,
        longitude=116.4,
        is_default=1,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


async def create_test_shop(db, user_id):
    shop = Shop(
        user_id=user_id,
        name="测试店铺",
        address="测试地址",
        rating=4.5,
        status=1,
        monthly_sales=100,
        min_order_amount=10.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    return shop


async def create_test_product(db, shop_id, stock=100, price=25.0):
    product = Product(
        shop_id=shop_id,
        name="测试商品",
        price=price,
        stock=stock,
        sales=0,
        status=1,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


def auth_headers(user_id, role="USER"):
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def create_paid_order(db, client, user, shop, product, quantity=1):
    addr = await create_test_address(db, user.id)
    headers = auth_headers(user.id)

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": quantity,
    }, headers=headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
    }, headers=headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["id"]

    pay_res = await client.post(f"/api/v1/orders/{order_id}/pay", headers=headers)
    assert pay_res.status_code == 200

    return order_id


@pytest.mark.asyncio
async def test_bug5_cancel_order_restores_stock(db, client):
    user = await create_test_user(db)
    shop = await create_test_shop(db, user.id)
    product = await create_test_product(db, shop.id, stock=10, price=25.0)
    addr = await create_test_address(db, user.id)
    headers = auth_headers(user.id)

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": 3,
    }, headers=headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
    }, headers=headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["id"]

    await db.refresh(product)
    assert product.stock == 7

    cancel_res = await client.put(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200

    await db.refresh(product)
    assert product.stock == 10


@pytest.mark.asyncio
async def test_bug4_earnings_api_uses_correct_field(db, client):
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13800000002")
    await create_test_shop(db, shop_owner.id)

    headers = auth_headers(shop_owner.id, role="SHOP_OWNER")

    res = await client.get("/api/v1/shop/earnings/summary", headers=headers)
    assert res.status_code == 200
    assert res.json()["code"] == 0


@pytest.mark.asyncio
async def test_bug3_shop_reject_order_refunds(db, client):
    user = await create_test_user(db, phone="13800000003")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13800000004")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, stock=10, price=25.0)

    order_id = await create_paid_order(db, client, user, shop, product, quantity=1)

    wallet_result = await db.execute(
        __import__("sqlalchemy").select(Wallet).where(Wallet.user_id == user.id)
    )
    wallet_before = wallet_result.scalar_one()
    balance_before = wallet_before.balance

    shop_headers = auth_headers(shop_owner.id, role="SHOP_OWNER")
    reject_res = await client.put(
        f"/api/v1/shop/my/orders/{order_id}/reject",
        json={"reason": "无法制作"},
        headers=shop_headers,
    )
    assert reject_res.status_code == 200

    await db.refresh(wallet_before)
    assert wallet_before.balance > balance_before


@pytest.mark.asyncio
async def test_bug3_shop_reject_restores_stock(db, client):
    user = await create_test_user(db, phone="13800000005")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13800000006")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, stock=10, price=25.0)

    order_id = await create_paid_order(db, client, user, shop, product, quantity=3)

    await db.refresh(product)
    assert product.stock == 7

    shop_headers = auth_headers(shop_owner.id, role="SHOP_OWNER")
    reject_res = await client.put(
        f"/api/v1/shop/my/orders/{order_id}/reject",
        json={"reason": "缺货"},
        headers=shop_headers,
    )
    assert reject_res.status_code == 200

    await db.refresh(product)
    assert product.stock == 10


@pytest.mark.asyncio
async def test_bug1_order_timeout_correct_call(db):
    from app.tasks.order_timeout import OrderTimeoutTask
    task = OrderTimeoutTask(db)
    result = await task.cancel_expired_orders()
    assert isinstance(result, int)


@pytest.mark.asyncio
async def test_bug2_order_service_logger_exists():
    from app.services.order_service import logger
    assert logger is not None
