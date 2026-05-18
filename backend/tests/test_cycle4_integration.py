import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, ShopStatus, Product, Category, ProductStatus,
    Order, OrderItem, OrderStatus, Wallet, UserAddress, Review,
    RiderEarning, FundFlow,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_cycle4_integration.db"

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


async def create_user(db, role="USER", phone="18800000001"):
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


SHOP_ADDR = "北京市朝阳区测试街道123号"
USER_ADDR = "北京市海淀区中关村大街1号"


@pytest.mark.asyncio
async def test_full_order_lifecycle_with_review(db, client):
    user = await create_user(db, role="USER", phone="18800000001")
    shop_owner = await create_user(db, role="SHOP_OWNER", phone="18800000002")
    rider = await create_user(db, role="RIDER", phone="18800000003")
    admin = await create_user(db, role="ADMIN", phone="18800000004")

    user_h = auth_headers(user.id, role="USER")
    shop_h = auth_headers(shop_owner.id, role="SHOP_OWNER")
    rider_h = auth_headers(rider.id, role="RIDER")
    admin_h = auth_headers(admin.id, role="ADMIN")

    apply_res = await client.post("/api/v1/shop/apply", json={
        "name": "集成测试店铺",
        "address": SHOP_ADDR,
    }, headers=shop_h)
    assert apply_res.status_code == 200
    shop_id = apply_res.json()["data"]["id"]

    approve_res = await client.put(f"/api/v1/admin/shop/{shop_id}/approve", headers=admin_h)
    assert approve_res.status_code == 200

    cat_res = await client.post("/api/v1/shop/category", json={
        "shop_id": shop_id,
        "name": "热销",
        "sort_order": 1,
    }, headers=shop_h)
    cat_id = None
    if cat_res.status_code == 200:
        cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post("/api/v1/shop/product", json={
        "shop_id": shop_id,
        "name": "测试商品",
        "price": 30.0,
        "stock": 50,
        "status": 1,
    }, headers=shop_h)
    assert prod_res.status_code == 200
    product_id = prod_res.json()["data"]["id"]

    addr_res = await client.post("/api/v1/users/addresses", json={
        "contact_name": "测试收货人",
        "contact_phone": "13800138000",
        "address": USER_ADDR,
        "is_default": 1,
    }, headers=user_h)
    assert addr_res.status_code == 200
    addr_id = addr_res.json()["data"]["id"]

    cart_res = await client.post("/api/v1/orders/cart", json={
        "shop_id": shop_id,
        "product_id": product_id,
        "quantity": 2,
    }, headers=user_h)
    assert cart_res.status_code == 200

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr_id,
        "shop_id": shop_id,
    }, headers=user_h)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["id"]
    assert order_res.json()["data"]["status"] == "PENDING_PAYMENT"

    pay_res = await client.post(f"/api/v1/orders/{order_id}/pay", headers=user_h)
    assert pay_res.status_code == 200
    assert pay_res.json()["data"]["status"] == "PENDING_ACCEPT"

    accept_res = await client.put(f"/api/v1/shop/my/orders/{order_id}/accept", headers=shop_h)
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "ACCEPTED"

    ready_res = await client.put(f"/api/v1/shop/my/orders/{order_id}/ready", headers=shop_h)
    assert ready_res.status_code == 200
    assert ready_res.json()["data"]["status"] == "READY"

    grab_res = await client.put(f"/api/v1/rider/orders/{order_id}/accept", headers=rider_h)
    assert grab_res.status_code == 200
    assert grab_res.json()["data"]["status"] == "DELIVERING"

    deliver_res = await client.put(f"/api/v1/rider/orders/{order_id}/deliver", headers=rider_h)
    assert deliver_res.status_code == 200
    assert deliver_res.json()["data"]["status"] == "DELIVERED"

    confirm_res = await client.put(f"/api/v1/orders/{order_id}/confirm", headers=user_h)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["data"]["status"] == "COMPLETED"

    review_res = await client.post("/api/v1/reviews", json={
        "order_id": order_id,
        "shop_rating": 5,
        "rider_rating": 4,
        "content": "非常好吃，配送也快！",
    }, headers=user_h)
    assert review_res.status_code == 200
    assert review_res.json()["data"]["shop_rating"] == 5
    assert review_res.json()["data"]["rider_rating"] == 4

    shop_reviews_res = await client.get(f"/api/v1/reviews/shop/{shop_id}")
    assert shop_reviews_res.status_code == 200
    assert shop_reviews_res.json()["data"]["total"] >= 1

    order_review_res = await client.get(f"/api/v1/reviews/order/{order_id}")
    assert order_review_res.status_code == 200
    assert order_review_res.json()["data"]["shop_rating"] == 5


@pytest.mark.asyncio
async def test_admin_shop_approval_and_stats(db, client):
    shop_owner = await create_user(db, role="SHOP_OWNER", phone="18800000010")
    admin = await create_user(db, role="ADMIN", phone="18800000011")
    user = await create_user(db, role="USER", phone="18800000012")

    shop_h = auth_headers(shop_owner.id, role="SHOP_OWNER")
    admin_h = auth_headers(admin.id, role="ADMIN")

    apply_res = await client.post("/api/v1/shop/apply", json={
        "name": "待审核店铺",
        "address": SHOP_ADDR,
    }, headers=shop_h)
    assert apply_res.status_code == 200
    shop_id = apply_res.json()["data"]["id"]
    assert apply_res.json()["data"]["status"] in (0, "PENDING")

    pending_res = await client.get("/api/v1/admin/shop/pending", headers=admin_h)
    assert pending_res.status_code == 200
    assert pending_res.json()["data"]["total"] >= 1

    approve_res = await client.put(f"/api/v1/admin/shop/{shop_id}/approve", headers=admin_h)
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] in (1, "APPROVED")

    stats_res = await client.get("/api/v1/admin/stats", headers=admin_h)
    assert stats_res.status_code == 200
    data = stats_res.json()["data"]
    assert data["user_count"] >= 3
    assert data["shop_count"] >= 1
    assert data["approved_shop_count"] >= 1

    users_res = await client.get("/api/v1/admin/users?role=ADMIN", headers=admin_h)
    assert users_res.status_code == 200
    assert users_res.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_wallet_and_transactions_flow(db, client):
    admin = await create_user(db, role="ADMIN", phone="18800000020")
    user = await create_user(db, role="USER", phone="18800000021")

    admin_h = auth_headers(admin.id, role="ADMIN")
    user_h = auth_headers(user.id, role="USER")

    wallet_res = await client.get("/api/v1/wallet", headers=user_h)
    assert wallet_res.status_code == 200
    assert wallet_res.json()["data"]["balance"] == 1000.0

    recharge_res = await client.post(f"/api/v1/wallet/recharge/{user.id}?amount=500", headers=admin_h)
    assert recharge_res.status_code == 200

    wallet_after = await client.get("/api/v1/wallet", headers=user_h)
    assert wallet_after.json()["data"]["balance"] == 1500.0

    tx_res = await client.get("/api/v1/wallet/transactions", headers=user_h)
    assert tx_res.status_code == 200
    assert tx_res.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_user_address_crud(db, client):
    user = await create_user(db, role="USER", phone="18800000030")
    user_h = auth_headers(user.id, role="USER")

    me_res = await client.get("/api/v1/users/me", headers=user_h)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["phone"] == "18800000030"

    update_res = await client.put("/api/v1/users/me", json={
        "nickname": "新昵称",
    }, headers=user_h)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["nickname"] == "新昵称"

    addr1_res = await client.post("/api/v1/users/addresses", json={
        "contact_name": "收货人1",
        "contact_phone": "13800000001",
        "address": USER_ADDR,
        "is_default": 1,
    }, headers=user_h)
    assert addr1_res.status_code == 200
    addr1_id = addr1_res.json()["data"]["id"]

    addr2_res = await client.post("/api/v1/users/addresses", json={
        "contact_name": "收货人2",
        "contact_phone": "13800000002",
        "address": "上海市浦东新区陆家嘴环路100号",
        "is_default": 1,
    }, headers=user_h)
    assert addr2_res.status_code == 200

    list_res = await client.get("/api/v1/users/addresses", headers=user_h)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 2

    update_addr_res = await client.put(f"/api/v1/users/addresses/{addr1_id}", json={
        "contact_name": "更新收货人",
    }, headers=user_h)
    assert update_addr_res.status_code == 200
    assert update_addr_res.json()["data"]["contact_name"] == "更新收货人"

    del_res = await client.delete(f"/api/v1/users/addresses/{addr1_id}", headers=user_h)
    assert del_res.status_code == 200

    list_after = await client.get("/api/v1/users/addresses", headers=user_h)
    assert len(list_after.json()["data"]) == 1


@pytest.mark.asyncio
async def test_shop_reject_order_refunds_and_restores_stock(db, client):
    user = await create_user(db, role="USER", phone="18800000040")
    shop_owner = await create_user(db, role="SHOP_OWNER", phone="18800000041")
    admin = await create_user(db, role="ADMIN", phone="18800000042")

    user_h = auth_headers(user.id, role="USER")
    shop_h = auth_headers(shop_owner.id, role="SHOP_OWNER")
    admin_h = auth_headers(admin.id, role="ADMIN")

    apply_res = await client.post("/api/v1/shop/apply", json={
        "name": "拒单测试店铺",
        "address": SHOP_ADDR,
    }, headers=shop_h)
    assert apply_res.status_code == 200
    shop_id = apply_res.json()["data"]["id"]
    await client.put(f"/api/v1/admin/shop/{shop_id}/approve", headers=admin_h)

    prod_res = await client.post("/api/v1/shop/product", json={
        "shop_id": shop_id,
        "name": "测试商品",
        "price": 50.0,
        "stock": 10,
        "status": 1,
    }, headers=shop_h)
    assert prod_res.status_code == 200
    product_id = prod_res.json()["data"]["id"]

    addr_res = await client.post("/api/v1/users/addresses", json={
        "contact_name": "收货人",
        "contact_phone": "13800000000",
        "address": USER_ADDR,
        "is_default": 1,
    }, headers=user_h)
    assert addr_res.status_code == 200
    addr_id = addr_res.json()["data"]["id"]

    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop_id,
        "product_id": product_id,
        "quantity": 3,
    }, headers=user_h)

    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": addr_id,
        "shop_id": shop_id,
    }, headers=user_h)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/pay", headers=user_h)

    wallet_before = await client.get("/api/v1/wallet", headers=user_h)
    balance_before = wallet_before.json()["data"]["balance"]

    reject_res = await client.put(
        f"/api/v1/shop/my/orders/{order_id}/reject",
        json={"reason": "库存不足"},
        headers=shop_h,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "CANCELLED"

    wallet_after = await client.get("/api/v1/wallet", headers=user_h)
    balance_after = wallet_after.json()["data"]["balance"]
    assert balance_after > balance_before
