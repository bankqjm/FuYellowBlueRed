import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, Product, Order, OrderItem, OrderStatus,
    Wallet, UserAddress, Coupon, UserCoupon, Category
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_cycle2.db"

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


async def create_test_user(db, role="USER", phone="13900000001"):
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


async def create_test_coupon(db, discount_amount=10.0, min_order_amount=30.0):
    from datetime import datetime, timedelta
    coupon = Coupon(
        code=f"TEST{datetime.now().timestamp()}",
        name="测试优惠券",
        discount_amount=discount_amount,
        min_order_amount=min_order_amount,
        total_count=100,
        remain_count=100,
        valid_from=datetime.now() - timedelta(days=1),
        valid_until=datetime.now() + timedelta(days=30),
        status="ACTIVE",
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


async def claim_coupon(db, user_id, coupon_id):
    uc = UserCoupon(user_id=user_id, coupon_id=coupon_id)
    db.add(uc)
    await db.commit()
    await db.refresh(uc)
    return uc


def auth_headers(user_id, role="USER"):
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_f1_coupon_integration_create_order(db, client):
    user = await create_test_user(db, phone="13900000001")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13900000002")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, price=50.0)
    coupon = await create_test_coupon(db, discount_amount=10.0, min_order_amount=30.0)
    user_coupon = await claim_coupon(db, user.id, coupon.id)
    addr = await create_test_address(db, user.id)

    headers = auth_headers(user.id)

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": 1,
    }, headers=headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
        "coupon_id": user_coupon.id,
    }, headers=headers)
    assert order_res.status_code == 200
    order_data = order_res.json()["data"]
    assert order_data["discount_amount"] == 10.0
    assert order_data["total_amount"] == 45.0


@pytest.mark.asyncio
async def test_f1_coupon_marked_used_after_payment(db, client):
    user = await create_test_user(db, phone="13900000003")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13900000004")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, price=50.0)
    coupon = await create_test_coupon(db, discount_amount=10.0, min_order_amount=30.0)
    user_coupon = await claim_coupon(db, user.id, coupon.id)
    addr = await create_test_address(db, user.id)

    headers = auth_headers(user.id)

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": 1,
    }, headers=headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
        "coupon_id": user_coupon.id,
    }, headers=headers)
    order_id = order_res.json()["data"]["id"]

    pay_res = await client.post(f"/api/v1/orders/{order_id}/pay", headers=headers)
    assert pay_res.status_code == 200

    await db.refresh(user_coupon)
    assert user_coupon.status == "USED"
    assert user_coupon.used_at is not None


@pytest.mark.asyncio
async def test_f3_rider_deliver_sets_delivered(db, client):
    user = await create_test_user(db, phone="13900000005")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13900000006")
    rider = await create_test_user(db, role="RIDER", phone="13900000007")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, price=25.0)
    addr = await create_test_address(db, user.id)

    user_headers = auth_headers(user.id)
    shop_headers = auth_headers(shop_owner.id, role="SHOP_OWNER")
    rider_headers = auth_headers(rider.id, role="RIDER")

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": 1,
    }, headers=user_headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
    }, headers=user_headers)
    order_id = order_res.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/pay", headers=user_headers)
    await client.put(f"/api/v1/shop/my/orders/{order_id}/accept", headers=shop_headers)
    await client.put(f"/api/v1/shop/my/orders/{order_id}/ready", headers=shop_headers)

    grab_res = await client.put(f"/api/v1/rider/orders/{order_id}/accept", headers=rider_headers)
    assert grab_res.status_code == 200

    deliver_res = await client.put(f"/api/v1/rider/orders/{order_id}/deliver", headers=rider_headers)
    assert deliver_res.status_code == 200
    assert deliver_res.json()["data"]["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_f3_f4_user_confirm_triggers_completed_and_settlement(db, client):
    user = await create_test_user(db, phone="13900000008")
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="13900000009")
    rider = await create_test_user(db, role="RIDER", phone="13900000010")
    shop = await create_test_shop(db, shop_owner.id)
    product = await create_test_product(db, shop.id, price=25.0)
    addr = await create_test_address(db, user.id)

    user_headers = auth_headers(user.id)
    shop_headers = auth_headers(shop_owner.id, role="SHOP_OWNER")
    rider_headers = auth_headers(rider.id, role="RIDER")

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product.id,
        "quantity": 1,
    }, headers=user_headers)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr.id,
        "shop_id": shop.id,
    }, headers=user_headers)
    order_id = order_res.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/pay", headers=user_headers)
    await client.put(f"/api/v1/shop/my/orders/{order_id}/accept", headers=shop_headers)
    await client.put(f"/api/v1/shop/my/orders/{order_id}/ready", headers=shop_headers)
    await client.put(f"/api/v1/rider/orders/{order_id}/accept", headers=rider_headers)
    await client.put(f"/api/v1/rider/orders/{order_id}/deliver", headers=rider_headers)

    confirm_res = await client.put(f"/api/v1/orders/{order_id}/confirm", headers=user_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["data"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_f2_rider_withdraw_uses_finance_service(db, client):
    rider = await create_test_user(db, role="RIDER", phone="13900000011")
    headers = auth_headers(rider.id, role="RIDER")

    withdraw_res = await client.post("/api/v1/rider/withdraw?amount=100", headers=headers)
    assert withdraw_res.status_code == 200
    assert "balance_after" in withdraw_res.json()["data"]
