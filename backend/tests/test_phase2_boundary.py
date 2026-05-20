"""Boundary value tests for amount, stock, pagination, and recharge limits.

Tests cover edge cases at the Pydantic Schema validation layer and
the business logic layer:
- 0, negative, and overflow amounts
- 0 stock products
- Pagination boundary parameters
- Recharge limit boundaries
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient

from app.models.models import (
    User, Shop, Product, Category, Wallet, UserAddress,
    ShopStatus, ProductStatus,
)
from app.utils.auth import hash_password


@pytest_asyncio.fixture
async def boundary_test_data(db_session):
    """Create test data for boundary tests."""
    # Create user with wallet (balance = 100.00)
    user = User(
        phone="13800009999",
        password_hash=hash_password("Test123456"),
        nickname="边界测试用户",
        role="USER",
        status=1,
    )
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id, balance=Decimal("100.00"), frozen_balance=Decimal("0.00"))
    db_session.add(wallet)
    await db_session.flush()

    # Create shop owner
    owner = User(
        phone="13800008888",
        password_hash=hash_password("Test123456"),
        nickname="边界测试商家",
        role="SHOP_OWNER",
        status=1,
    )
    db_session.add(owner)
    await db_session.flush()

    # Create rider
    rider = User(
        phone="13800007777",
        password_hash=hash_password("Test123456"),
        nickname="边界测试骑手",
        role="RIDER",
        status=1,
    )
    db_session.add(rider)
    await db_session.flush()

    rider_wallet = Wallet(user_id=rider.id, balance=Decimal("50.00"), frozen_balance=Decimal("0.00"))
    db_session.add(rider_wallet)
    await db_session.flush()

    # Create shop
    shop = Shop(
        user_id=owner.id,
        name="边界测试店铺",
        address="测试地址",
        status=ShopStatus.APPROVED.value,
        rating=5.0,
    )
    db_session.add(shop)
    await db_session.flush()

    # Create category
    category = Category(shop_id=shop.id, name="测试分类", sort_order=1)
    db_session.add(category)
    await db_session.flush()

    # Create product with 0 stock
    product_zero = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="零库存商品",
        price=Decimal("10.00"),
        stock=0,
        status=ProductStatus.ON.value,
    )
    db_session.add(product_zero)
    await db_session.flush()

    # Create product with normal stock
    product_normal = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="正常商品",
        price=Decimal("25.00"),
        stock=100,
        status=ProductStatus.ON.value,
    )
    db_session.add(product_normal)
    await db_session.flush()

    # Create address
    address = UserAddress(
        user_id=user.id,
        contact_name="测试",
        contact_phone="13800009999",
        address="测试地址",
        is_default=1,
    )
    db_session.add(address)
    await db_session.flush()

    await db_session.commit()

    return {
        "user": user,
        "owner": owner,
        "rider": rider,
        "shop": shop,
        "product_zero": product_zero,
        "product_normal": product_normal,
        "wallet": wallet,
        "address": address,
    }


# ============ Amount Boundary Tests ============


@pytest.mark.asyncio
async def test_recharge_zero_amount(client, boundary_test_data):
    """Recharge with 0 amount should be rejected."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/wallet/recharge", json={"amount": 0}, headers=headers)
    assert res.status_code == 400, "Zero recharge should be rejected"


@pytest.mark.asyncio
async def test_recharge_negative_amount(client, boundary_test_data):
    """Recharge with negative amount should be rejected."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/wallet/recharge", json={"amount": -10}, headers=headers)
    # Pydantic should reject or business logic should reject
    assert res.status_code in (400, 422), "Negative recharge should be rejected"


@pytest.mark.asyncio
async def test_recharge_over_limit(client, boundary_test_data):
    """Recharge over single limit (10000) should be rejected."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/wallet/recharge", json={"amount": 10000.01}, headers=headers)
    assert res.status_code == 400, "Over-limit recharge should be rejected"


@pytest.mark.asyncio
async def test_withdraw_insufficient_balance(client, boundary_test_data):
    """Withdraw more than balance should be rejected."""
    # Login as rider (has 50.00 balance)
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800007777",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/wallet/withdraw", json={
        "amount": 100.00,
        "method": "ALIPAY",
        "account": "test@example.com",
    }, headers=headers)
    assert res.status_code == 400, "Withdraw exceeding balance should be rejected"


# ============ Stock Boundary Tests ============


@pytest.mark.asyncio
async def test_order_zero_stock_product(client, boundary_test_data):
    """Ordering a product with 0 stock should be rejected."""
    data = boundary_test_data
    product_zero = data["product_zero"]
    shop = data["shop"]
    address = data["address"]

    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add to cart
    await client.post("/api/v1/orders/cart", json={
        "shop_id": shop.id,
        "product_id": product_zero.id,
        "quantity": 1,
    }, headers=headers)

    # Try to create order (note: endpoint is /orders/create)
    order_res = await client.post("/api/v1/orders/create", json={
        "address_id": address.id,
        "shop_id": shop.id,
    }, headers=headers)

    # Should fail with "库存不足"
    res_data = order_res.json()
    assert res_data.get("code") != 0 or "库存" in res_data.get("message", ""), \
        "Ordering 0-stock product should fail"


# ============ Pagination Boundary Tests ============


@pytest.mark.asyncio
async def test_pagination_page_zero(client, boundary_test_data):
    """Page=0 should be rejected by Pydantic validation (ge=1)."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/orders?page=0", headers=headers)
    assert res.status_code == 422, "Page=0 should fail validation"


@pytest.mark.asyncio
async def test_pagination_negative_page(client, boundary_test_data):
    """Page=-1 should be rejected by Pydantic validation (ge=1)."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/orders?page=-1", headers=headers)
    assert res.status_code == 422, "Negative page should fail validation"


@pytest.mark.asyncio
async def test_pagination_large_page_size(client, boundary_test_data):
    """page_size=1000 should be capped at 100 by Pydantic validation (le=100)."""
    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "13800009999",
        "password": "Test123456",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/orders?page_size=1000", headers=headers)
    assert res.status_code == 422, "page_size=1000 should fail validation (max 100)"


# ============ Password Strength Boundary Tests ============


@pytest.mark.asyncio
async def test_register_weak_password_no_lowercase(client):
    """Registration with password missing lowercase should fail."""
    res = await client.post("/api/v1/auth/register", json={
        "phone": "13800009998",
        "password": "TEST123456",
        "confirm_password": "TEST123456",
        "nickname": "弱密码测试",
    })
    assert res.status_code == 422 or "小写" in res.json().get("detail", [{}])[0].get("msg", ""), \
        "Password without lowercase should be rejected"


@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(client):
    """Registration with password missing uppercase should fail."""
    res = await client.post("/api/v1/auth/register", json={
        "phone": "13800009997",
        "password": "test123456",
        "confirm_password": "test123456",
        "nickname": "弱密码测试",
    })
    assert res.status_code == 422, "Password without uppercase should be rejected"


@pytest.mark.asyncio
async def test_register_weak_password_no_digit(client):
    """Registration with password missing digits should fail."""
    res = await client.post("/api/v1/auth/register", json={
        "phone": "13800009996",
        "password": "TestPassword",
        "confirm_password": "TestPassword",
        "nickname": "弱密码测试",
    })
    assert res.status_code == 422, "Password without digits should be rejected"


@pytest.mark.asyncio
async def test_register_weak_password_too_short(client):
    """Registration with password < 8 chars should fail."""
    res = await client.post("/api/v1/auth/register", json={
        "phone": "13800009995",
        "password": "Abc12",
        "confirm_password": "Abc12",
        "nickname": "短密码测试",
    })
    assert res.status_code == 422, "Password < 8 chars should be rejected"
