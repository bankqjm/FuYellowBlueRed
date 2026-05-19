import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, ShopStatus, Product, Category, ProductStatus,
    Order, OrderItem, OrderStatus, UserAddress,
    Wallet, RiderEarning, EarningType,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_rider.db"

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


async def create_ready_order(db, user, shop, product):
    address = UserAddress(
        user_id=user.id,
        contact_name="测试收货人",
        contact_phone=user.phone,
        address="测试收货地址",
        is_default=1,
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)

    order_no = uuid.uuid4().hex[:32]
    order = Order(
        order_no=order_no,
        user_id=user.id,
        shop_id=shop.id,
        address=address.address,
        phone=address.contact_phone,
        total_amount=product.price + shop.delivery_fee,
        delivery_fee=shop.delivery_fee,
        status=OrderStatus.READY,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        product_image=product.image,
        price=product.price,
        quantity=1,
    )
    db.add(order_item)
    await db.commit()
    return order


@pytest.mark.asyncio
async def test_get_available_orders(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200001")
    user = await create_test_user(db, role="USER", phone="19900200002")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200003")
    shop = Shop(
        user_id=owner.id,
        name="骑手测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers = auth_headers(rider.id, role="RIDER")
    res = await client.get("/api/v1/rider/orders/available", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    order_ids = [item["id"] for item in data["items"]]
    assert order.id in order_ids


@pytest.mark.asyncio
async def test_get_available_orders_non_rider(db, client):
    user = await create_test_user(db, role="USER", phone="19900200004")

    headers = auth_headers(user.id, role="USER")
    res = await client.get("/api/v1/rider/orders/available", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_accept_order(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200005")
    user = await create_test_user(db, role="USER", phone="19900200006")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200007")
    shop = Shop(
        user_id=owner.id,
        name="接单测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers = auth_headers(rider.id, role="RIDER")
    res = await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == OrderStatus.DELIVERING.value
    assert data["rider_id"] == rider.id


@pytest.mark.asyncio
async def test_accept_order_already_taken(db, client):
    rider1 = await create_test_user(db, role="RIDER", phone="19900200008")
    rider2 = await create_test_user(db, role="RIDER", phone="19900200009")
    user = await create_test_user(db, role="USER", phone="19900200010")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200011")
    shop = Shop(
        user_id=owner.id,
        name="重复接单测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers1 = auth_headers(rider1.id, role="RIDER")
    res1 = await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers1)
    assert res1.status_code == 200

    headers2 = auth_headers(rider2.id, role="RIDER")
    res2 = await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers2)
    assert res2.status_code == 400


@pytest.mark.asyncio
async def test_deliver_order(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200012")
    user = await create_test_user(db, role="USER", phone="19900200013")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200014")
    shop = Shop(
        user_id=owner.id,
        name="送达测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers = auth_headers(rider.id, role="RIDER")
    await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers)

    res = await client.put(f"/api/v1/rider/orders/{order.id}/deliver", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == OrderStatus.DELIVERED.value


@pytest.mark.asyncio
async def test_get_earnings_summary(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200015")
    user = await create_test_user(db, role="USER", phone="19900200016")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200017")
    shop = Shop(
        user_id=owner.id,
        name="收入测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    earning = RiderEarning(
        rider_id=rider.id,
        order_id=order.id,
        amount=4.0,
        type=EarningType.DELIVERY_FEE.value,
    )
    db.add(earning)
    await db.commit()

    headers = auth_headers(rider.id, role="RIDER")
    res = await client.get("/api/v1/rider/earnings/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_earnings" in data
    assert "balance" in data
    assert data["total_earnings"] > 0


@pytest.mark.asyncio
async def test_withdraw(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200018")
    user = await create_test_user(db, role="USER", phone="19900200019")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200020")
    shop = Shop(
        user_id=owner.id,
        name="提现测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers = auth_headers(rider.id, role="RIDER")
    await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers)
    await client.put(f"/api/v1/rider/orders/{order.id}/deliver", headers=headers)

    res = await client.post("/api/v1/rider/withdraw?amount=10.0", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "withdraw_id" in data
    assert data["amount"] == 10.0


@pytest.mark.asyncio
async def test_get_withdrawal_records(db, client):
    rider = await create_test_user(db, role="RIDER", phone="19900200021")
    user = await create_test_user(db, role="USER", phone="19900200022")
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19900200023")
    shop = Shop(
        user_id=owner.id,
        name="提现记录测试店铺",
        address="测试地址",
        rating=5.0,
        status=ShopStatus.APPROVED.value,
        monthly_sales=0,
        min_order_amount=20.0,
        delivery_fee=5.0,
        delivery_time="30分钟",
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类", sort_order=0)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=30.0,
        stock=100,
        status=ProductStatus.ON.value,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    order = await create_ready_order(db, user, shop, product)

    headers = auth_headers(rider.id, role="RIDER")
    await client.put(f"/api/v1/rider/orders/{order.id}/accept", headers=headers)
    await client.put(f"/api/v1/rider/orders/{order.id}/deliver", headers=headers)
    await client.post("/api/v1/rider/withdraw?amount=10.0", headers=headers)

    res = await client.get("/api/v1/rider/withdrawals", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["amount"] == 10.0
