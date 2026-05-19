import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, Order, OrderStatus, ShopStatus, Wallet, Review,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_review.db"

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
async def test_create_review(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000001")
    user = await create_test_user(db, role="USER", phone="19920000002")
    headers = auth_headers(user.id, role="USER")

    shop = Shop(
        user_id=owner.id,
        name="评价店铺",
        address="评价地址100号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD101",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000101",
        total_amount=50.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    res = await client.post("/api/v1/reviews", json={
        "order_id": order.id,
        "shop_rating": 5,
        "rider_rating": 4,
        "content": "非常好吃",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["shop_rating"] == 5
    assert data["rider_rating"] == 4
    assert data["content"] == "非常好吃"


@pytest.mark.asyncio
async def test_create_review_non_completed_order(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000003")
    user = await create_test_user(db, role="USER", phone="19920000004")
    headers = auth_headers(user.id, role="USER")

    shop = Shop(
        user_id=owner.id,
        name="未完成店铺",
        address="未完成地址200号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD102",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000102",
        total_amount=30.0,
        status=OrderStatus.ACCEPTED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    res = await client.post("/api/v1/reviews", json={
        "order_id": order.id,
        "shop_rating": 3,
        "content": "还没完成",
    }, headers=headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_create_review_duplicate(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000005")
    user = await create_test_user(db, role="USER", phone="19920000006")
    headers = auth_headers(user.id, role="USER")

    shop = Shop(
        user_id=owner.id,
        name="重复评价店铺",
        address="重复评价地址300号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD103",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000103",
        total_amount=40.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    review = Review(
        order_id=order.id,
        user_id=user.id,
        shop_id=shop.id,
        shop_rating=4,
        content="已评价",
    )
    db.add(review)
    await db.commit()

    res = await client.post("/api/v1/reviews", json={
        "order_id": order.id,
        "shop_rating": 5,
        "content": "再次评价",
    }, headers=headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_get_shop_reviews(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000007")
    user = await create_test_user(db, role="USER", phone="19920000008")

    shop = Shop(
        user_id=owner.id,
        name="店铺评价列表",
        address="评价列表地址400号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD104",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000104",
        total_amount=60.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    review = Review(
        order_id=order.id,
        user_id=user.id,
        shop_id=shop.id,
        shop_rating=5,
        content="好评",
    )
    db.add(review)
    await db.commit()

    res = await client.get(f"/api/v1/reviews/shop/{shop.id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["shop_rating"] == 5


@pytest.mark.asyncio
async def test_get_order_review(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000009")
    user = await create_test_user(db, role="USER", phone="19920000010")

    shop = Shop(
        user_id=owner.id,
        name="订单评价店铺",
        address="订单评价地址500号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD105",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000105",
        total_amount=70.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    review = Review(
        order_id=order.id,
        user_id=user.id,
        shop_id=shop.id,
        shop_rating=4,
        content="不错",
    )
    db.add(review)
    await db.commit()

    res = await client.get(f"/api/v1/reviews/order/{order.id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["shop_rating"] == 4
    assert data["content"] == "不错"


@pytest.mark.asyncio
async def test_get_order_review_not_found(db, client):
    owner = await create_test_user(db, role="SHOP_OWNER", phone="19920000011")
    user = await create_test_user(db, role="USER", phone="19920000012")

    shop = Shop(
        user_id=owner.id,
        name="无评价店铺",
        address="无评价地址600号",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    order = Order(
        order_no="ORD106",
        user_id=user.id,
        shop_id=shop.id,
        address="用户地址",
        phone="13800000106",
        total_amount=80.0,
        status=OrderStatus.COMPLETED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    res = await client.get(f"/api/v1/reviews/order/{order.id}")
    assert res.status_code == 400
