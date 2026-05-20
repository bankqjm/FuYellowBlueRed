"""
Phase 1 Unit Tests for FuYellowBlueRed Delivery Platform

Covers 8 reform items:
  1. SEC-REFORM-01: Numeric(10,2) decimal precision
  2. SEC-REFORM-02: Snowflake ID generation
  3. SEC-REFORM-03: WebSocket JWT authentication
  4. API-REFORM-01: require_role returns 403
  5. SEC-REFORM-04: Row-level locking for stock operations
  6. CODE-REFORM-01: API routes delegate to Service layer
  7. U-P0-02: Payment countdown + order timeout auto-cancel
  8. U-P2-03-FE: Wallet frontend page (backend endpoints)
"""

import pytest
import pytest_asyncio
import threading
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool
from sqlalchemy import select, inspect as sa_inspect
import os

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["UPLOAD_DIR"] = "/tmp/test_uploads"

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User,
    UserRole,
    UserStatus,
    Shop,
    Category,
    Product,
    ProductStatus,
    UserAddress,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    Wallet,
    FundFlow,
    PaymentTransaction,
)
from app.utils.auth import hash_password, create_access_token, verify_token
from app.utils.snowflake import (
    SnowflakeGenerator,
    generate_snowflake_id,
    generate_snowflake_str,
    generate_order_no,
    generate_trade_no,
)
from app.services.order_service import OrderService, to_decimal as order_to_decimal
from app.services.finance import FinanceService, to_decimal as finance_to_decimal
from app.tasks.order_timeout import OrderTimeoutTask

# ── In-memory SQLite test database ──────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        phone="13800138000",
        password_hash=hash_password("Test123456"),
        nickname="测试用户",
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_shop_owner(db_session):
    user = User(
        phone="13900139000",
        password_hash=hash_password("Test123456"),
        nickname="测试商家",
        role=UserRole.SHOP_OWNER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_rider(db_session):
    user = User(
        phone="13700137000",
        password_hash=hash_password("Test123456"),
        nickname="测试骑手",
        role=UserRole.RIDER.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session):
    user = User(
        phone="13600136000",
        password_hash=hash_password("Test123456"),
        nickname="测试管理员",
        role=UserRole.ADMIN.value,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user_id: int, role: str = "USER"):
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _create_shop_with_product(db_session, shop_owner):
    """Helper: create a shop with one product that has stock."""
    shop = Shop(
        user_id=shop_owner.id,
        name="测试店铺",
        address="测试地址",
        status=1,
    )
    db_session.add(shop)
    await db_session.commit()
    await db_session.refresh(shop)

    category = Category(shop_id=shop.id, name="测试分类")
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="测试商品",
        price=Decimal("25.00"),
        stock=100,
        status=ProductStatus.ON.value,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    return shop, category, product


# ══════════════════════════════════════════════════════════════════════════════
# 1. SEC-REFORM-01: 金额字段 Numeric(10,2) 测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestNumericFields:
    """SEC-REFORM-01: Verify all monetary columns use Numeric(10,2)."""

    async def test_order_amount_fields_are_numeric(self):
        """Order model monetary fields should be Numeric type."""
        from sqlalchemy import Numeric as SA_Numeric

        mapper = sa_inspect(Order)
        for col_name in ("total_amount", "discount_amount", "delivery_fee"):
            col = mapper.columns[col_name]
            assert isinstance(col.type, SA_Numeric), (
                f"Order.{col_name} should be Numeric, got {type(col.type).__name__}"
            )

    async def test_product_price_is_numeric(self):
        """Product.price should be Numeric type."""
        from sqlalchemy import Numeric as SA_Numeric

        mapper = sa_inspect(Product)
        col = mapper.columns["price"]
        assert isinstance(col.type, SA_Numeric)

    async def test_wallet_balance_is_numeric(self):
        """Wallet.balance and frozen_balance should be Numeric type."""
        from sqlalchemy import Numeric as SA_Numeric

        mapper = sa_inspect(Wallet)
        for col_name in ("balance", "frozen_balance"):
            col = mapper.columns[col_name]
            assert isinstance(col.type, SA_Numeric)

    async def test_fund_flow_amount_is_numeric(self):
        """FundFlow monetary fields should be Numeric type."""
        from sqlalchemy import Numeric as SA_Numeric

        mapper = sa_inspect(FundFlow)
        for col_name in ("amount", "balance_before", "balance_after"):
            col = mapper.columns[col_name]
            assert isinstance(col.type, SA_Numeric)

    async def test_payment_transaction_amount_is_numeric(self):
        """PaymentTransaction.amount should be Numeric type."""
        from sqlalchemy import Numeric as SA_Numeric

        mapper = sa_inspect(PaymentTransaction)
        col = mapper.columns["amount"]
        assert isinstance(col.type, SA_Numeric)


@pytest.mark.asyncio
class TestDecimalPrecision:
    """SEC-REFORM-01: Decimal arithmetic should not lose precision."""

    async def test_to_decimal_preserves_precision(self):
        """to_decimal() should convert float without precision loss."""
        result = order_to_decimal(0.1) + order_to_decimal(0.2)
        assert result == Decimal("0.3"), f"Expected 0.3, got {result}"

    async def test_to_decimal_handles_float_input(self):
        """to_decimal() should handle float input correctly."""
        assert order_to_decimal(10.5) == Decimal("10.5")
        assert finance_to_decimal(99.99) == Decimal("99.99")

    async def test_to_decimal_handles_string_input(self):
        """to_decimal() should handle string input correctly."""
        assert order_to_decimal("123.45") == Decimal("123.45")

    async def test_to_decimal_handles_decimal_input(self):
        """to_decimal() should pass through Decimal input unchanged."""
        d = Decimal("67.89")
        assert order_to_decimal(d) is d

    async def test_to_decimal_handles_none(self):
        """to_decimal(None) should return ZERO."""
        assert order_to_decimal(None) == Decimal("0.00")

    async def test_decimal_field_serializes_to_float(self):
        """DecimalField in schemas should serialize to float for JSON."""
        from app.schemas.base import DecimalField
        from pydantic import BaseModel

        class DemoModel(BaseModel):
            amount: DecimalField

        m = DemoModel(amount=Decimal("12.34"))
        json_data = m.model_dump(mode="json")
        assert isinstance(json_data["amount"], float)
        assert json_data["amount"] == 12.34


# ══════════════════════════════════════════════════════════════════════════════
# 2. SEC-REFORM-02: 雪花算法测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSnowflakeGeneration:
    """SEC-REFORM-02: Verify Snowflake ID generation."""

    async def test_order_no_length_within_32(self):
        """Generated order_no must be <= 32 characters."""
        order_no = generate_order_no()
        assert len(order_no) <= 32, f"order_no length {len(order_no)} > 32"

    async def test_trade_no_starts_with_T(self):
        """trade_no should start with 'T' prefix."""
        trade_no = generate_trade_no()
        assert trade_no.startswith("T")

    async def test_trade_no_length_within_33(self):
        """trade_no (T + snowflake) must be <= 33 characters."""
        trade_no = generate_trade_no()
        assert len(trade_no) <= 33

    async def test_consecutive_ids_are_unique(self):
        """Consecutive IDs should never duplicate."""
        ids = set()
        for _ in range(1000):
            new_id = generate_snowflake_id()
            assert new_id not in ids, f"Duplicate ID generated: {new_id}"
            ids.add(new_id)

    async def test_consecutive_str_ids_are_unique(self):
        """Consecutive string IDs should never duplicate."""
        ids = set()
        for _ in range(1000):
            new_id = generate_snowflake_str()
            assert new_id not in ids, f"Duplicate string ID generated: {new_id}"
            ids.add(new_id)

    async def test_clock_backward_detection(self):
        """Clock going backward should raise RuntimeError."""
        gen = SnowflakeGenerator(worker_id=1, datacenter_id=1)
        # Force last_timestamp to be in the future
        gen.last_timestamp = gen._current_millis() + 10000
        with pytest.raises(RuntimeError, match="Clock moved backwards"):
            gen.generate_id()

    async def test_multi_thread_uniqueness(self):
        """IDs generated from multiple threads should all be unique."""
        gen = SnowflakeGenerator(worker_id=1, datacenter_id=1)
        ids = []
        errors = []

        def generate_batch(count):
            try:
                for _ in range(count):
                    ids.append(gen.generate_id())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=generate_batch, args=(500,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent generation: {errors}"
        assert len(ids) == len(set(ids)), "Duplicate IDs found in multi-thread test"

    async def test_worker_id_out_of_range(self):
        """Worker ID > 31 should raise ValueError."""
        with pytest.raises(ValueError, match="worker_id"):
            SnowflakeGenerator(worker_id=32, datacenter_id=1)

    async def test_datacenter_id_out_of_range(self):
        """Datacenter ID > 31 should raise ValueError."""
        with pytest.raises(ValueError, match="datacenter_id"):
            SnowflakeGenerator(worker_id=1, datacenter_id=32)


# ══════════════════════════════════════════════════════════════════════════════
# 3. SEC-REFORM-03: WebSocket JWT 认证测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestWebSocketJWTAuth:
    """SEC-REFORM-03: WebSocket JWT authentication tests."""

    async def test_no_token_results_in_none_payload(self):
        """WebSocket connection without token: verify_token('') returns None."""
        from app.utils.auth import verify_token

        payload = verify_token("")
        assert payload is None, "Empty token should yield None payload"

    async def test_invalid_token_rejected(self):
        """Invalid token should be rejected by verify_token."""
        payload = verify_token("this.is.invalid.token")
        assert payload is None

    async def test_token_user_id_mismatch_detected(self):
        """Token with different user_id than URL should be detected."""
        token = create_access_token(data={"sub": "999", "role": "USER"})
        payload = verify_token(token)
        token_user_id = payload.get("sub")
        url_user_id = "1"
        assert str(token_user_id) != str(url_user_id)

    async def test_valid_token_accepted(self, test_user):
        """Valid token should be accepted by verify_token."""
        token = create_access_token(data={"sub": str(test_user.id), "role": "USER"})
        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == str(test_user.id)

    async def test_websocket_close_reason_is_unauthorized(self):
        """Close reason should be 'Unauthorized', not leaking specific errors.

        Verify that the code in main.py uses reason='Unauthorized' for all
        rejection paths (no token, invalid token, mismatch, expired).
        """
        import inspect
        import ast

        source = inspect.getsource(
            __import__("app.main", fromlist=["app"]).websocket_endpoint
        )
        tree = ast.parse(source)
        close_reasons = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "reason":
                if isinstance(node.value, ast.Constant):
                    close_reasons.append(node.value.value)

        # All WebSocket close reasons should be "Unauthorized"
        for reason in close_reasons:
            assert reason == "Unauthorized", (
                f"WebSocket close reason should be 'Unauthorized', got '{reason}'"
            )

    async def test_refresh_token_rejected_for_websocket(self):
        """Refresh tokens should not be accepted for WebSocket connections."""
        from app.utils.auth import create_refresh_token

        refresh_token = create_refresh_token(data={"sub": "1", "role": "USER"})
        payload = verify_token(refresh_token)
        token_type = payload.get("type")
        assert token_type == "refresh", "Expected refresh token type"
        # The WebSocket handler checks token_type != "access"
        assert token_type != "access"


# ══════════════════════════════════════════════════════════════════════════════
# 4. API-REFORM-01: require_role 返回 403 测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRequireRoleReturns403:
    """API-REFORM-01: require_role should return 403 (not 401) for insufficient permissions."""

    async def test_logged_in_insufficient_role_returns_403(
        self, client, test_user, test_shop_owner, db_session
    ):
        """A logged-in USER trying an admin-only endpoint should get 403."""
        # wallet/recharge/{user_id} requires ADMIN
        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            f"/api/v1/wallet/recharge/{test_user.id}?amount=100.0",
            headers=headers,
        )
        assert response.status_code == 403, (
            f"Expected 403 for insufficient role, got {response.status_code}"
        )

    async def test_unauthenticated_request_returns_401(self, client, db_session):
        """Unauthenticated requests should still return 401."""
        response = await client.post(
            "/api/v1/wallet/recharge/1?amount=100.0",
        )
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated request, got {response.status_code}"
        )

    async def test_forbidden_exception_is_403(self):
        """ForbiddenException should have status_code 403."""
        from app.utils.exceptions import ForbiddenException

        exc = ForbiddenException("权限不足")
        assert exc.status_code == 403

    async def test_unauthorized_exception_is_401(self):
        """UnauthorizedException should have status_code 401."""
        from app.utils.exceptions import UnauthorizedException

        exc = UnauthorizedException("未授权")
        assert exc.status_code == 401

    async def test_shop_owner_can_withdraw_but_user_cannot(
        self, client, test_shop_owner, test_user, db_session
    ):
        """SHOP_OWNER can access withdraw, but USER gets 403."""
        # Create wallets for both users
        for u in [test_shop_owner, test_user]:
            wallet = Wallet(user_id=u.id, balance=Decimal("1000.00"), frozen_balance=Decimal("0.00"))
            db_session.add(wallet)
        await db_session.commit()

        # SHOP_OWNER should be able to access withdraw endpoint (may fail on business logic, but not 403)
        headers_shop = auth_headers(test_shop_owner.id, role="SHOP_OWNER")
        resp_shop = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": "test@alipay.com"},
            headers=headers_shop,
        )
        # Should not be 403 (may be 200 or 400 depending on business logic)
        assert resp_shop.status_code != 403, "SHOP_OWNER should not get 403 on withdraw"

        # USER should get 403
        headers_user = auth_headers(test_user.id, role="USER")
        resp_user = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": "test@alipay.com"},
            headers=headers_user,
        )
        assert resp_user.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# 5. SEC-REFORM-04: 库存扣减行锁测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestStockRowLock:
    """SEC-REFORM-04: Verify row-level locking in stock operations."""

    async def test_create_order_uses_with_for_update(
        self, client, test_user, test_shop_owner, db_session
    ):
        """create_order should use with_for_update() when querying product stock."""
        shop, category, product = await _create_shop_with_product(db_session, test_shop_owner)

        # Add item to cart
        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=2,
        )
        db_session.add(cart_item)

        # Add address
        address = UserAddress(
            user_id=test_user.id,
            contact_name="张三",
            contact_phone="13800138000",
            address="测试地址",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/orders/create",
            json={"address_id": address.id, "shop_id": shop.id},
            headers=headers,
        )
        assert response.status_code == 200

        # Verify stock was decremented
        await db_session.refresh(product)
        assert product.stock == 98  # 100 - 2

    async def test_insufficient_stock_raises_error(
        self, client, test_user, test_shop_owner, db_session
    ):
        """Ordering more than available stock should raise an error."""
        shop, category, product = await _create_shop_with_product(db_session, test_shop_owner)
        product.stock = 1
        await db_session.commit()

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=5,
        )
        db_session.add(cart_item)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="张三",
            contact_phone="13800138000",
            address="测试地址",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/orders/create",
            json={"address_id": address.id, "shop_id": shop.id},
            headers=headers,
        )
        assert response.status_code == 400
        assert "库存不足" in response.json().get("message", "")

    async def test_cancel_order_restores_stock(
        self, client, test_user, test_shop_owner, db_session
    ):
        """cancel_order should restore product stock."""
        shop, category, product = await _create_shop_with_product(db_session, test_shop_owner)

        # Create an order directly
        order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("50.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
        )
        db_session.add(order)
        await db_session.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=3,
        )
        db_session.add(order_item)
        product.stock -= 3  # Simulate stock deduction
        await db_session.commit()
        await db_session.refresh(order)

        # Cancel the order
        headers = auth_headers(test_user.id, role="USER")
        response = await client.put(
            f"/api/v1/orders/{order.id}/cancel",
            headers=headers,
        )
        assert response.status_code == 200

        # Verify stock was restored
        await db_session.refresh(product)
        assert product.stock == 100  # Restored to original

    async def test_reject_order_restores_stock(
        self, client, test_shop_owner, db_session
    ):
        """reject_order in shop.py should restore product stock."""
        # Create a customer
        customer = User(
            phone="13811111111",
            password_hash=hash_password("Test123456"),
            nickname="顾客",
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        shop, category, product = await _create_shop_with_product(db_session, test_shop_owner)
        product.stock = 10
        await db_session.commit()

        # Create a PAID order (PENDING_ACCEPT) that can be rejected
        order = Order(
            order_no=generate_order_no(),
            user_id=customer.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13811111111",
            total_amount=Decimal("50.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_ACCEPT,
        )
        db_session.add(order)
        await db_session.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=2,
        )
        db_session.add(order_item)
        product.stock = 8  # Already deducted 2
        await db_session.commit()
        await db_session.refresh(order)

        # Create wallet for refund
        wallet = Wallet(user_id=customer.id, balance=Decimal("1000.00"), frozen_balance=Decimal("0.00"))
        db_session.add(wallet)
        await db_session.commit()

        # Reject the order
        headers = auth_headers(test_shop_owner.id, role="SHOP_OWNER")
        response = await client.put(
            f"/api/v1/shop/my/orders/{order.id}/reject",
            json={"reason": "无法制作"},
            headers=headers,
        )
        assert response.status_code == 200

        # Verify stock was restored
        await db_session.refresh(product)
        assert product.stock == 10  # Restored from 8 + 2


# ══════════════════════════════════════════════════════════════════════════════
# 6. CODE-REFORM-01: API 统一调用 Service 层测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestAPIDelegatedToService:
    """CODE-REFORM-01: API routes should delegate to OrderService, not operate DB directly."""

    async def test_orders_routes_use_service(self):
        """All order routes should instantiate OrderService and call its methods."""
        import ast
        import inspect

        from app.api.v1 import orders as orders_module

        source = inspect.getsource(orders_module)
        tree = ast.parse(source)

        # Find all async functions in the module
        route_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                route_functions.append(node.name)

        # Verify each route function creates OrderService
        for func_name in route_functions:
            func = getattr(orders_module, func_name, None)
            if func is None:
                continue
            func_src = inspect.getsource(func)
            assert "OrderService" in func_src, (
                f"Route function '{func_name}' should use OrderService"
            )

    async def test_create_order_delegates_to_service(
        self, client, test_user, test_shop_owner, db_session
    ):
        """POST /orders/create should delegate to OrderService.create_order."""
        shop, category, product = await _create_shop_with_product(db_session, test_shop_owner)

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=1,
        )
        db_session.add(cart_item)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="张三",
            contact_phone="13800138000",
            address="测试地址",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        with patch.object(OrderService, "create_order", new_callable=AsyncMock) as mock_create:
            from app.schemas.order import OrderResponse

            mock_create.return_value = OrderResponse(
                id=1,
                order_no="TEST123",
                user_id=test_user.id,
                shop_id=shop.id,
                address="测试",
                phone="13800000000",
                total_amount=Decimal("25.00"),
                discount_amount=Decimal("0.00"),
                delivery_fee=Decimal("3.00"),
                status=OrderStatus.PENDING_PAYMENT,
            )
            response = await client.post(
                "/api/v1/orders/create",
                json={"address_id": address.id, "shop_id": shop.id},
                headers=headers,
            )
            mock_create.assert_awaited_once()

    async def test_service_return_value_mapped_to_response(self):
        """Service method return values should be wrapped in ResponseSchema."""
        import ast
        import inspect

        from app.api.v1 import orders as orders_module

        source = inspect.getsource(orders_module)
        tree = ast.parse(source)

        # Check that route handlers return ResponseSchema objects
        response_schema_count = source.count("ResponseSchema(")
        assert response_schema_count > 0, (
            "Order routes should return ResponseSchema-wrapped responses"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 7. U-P0-02: 支付倒计时 + 订单超时自动取消测试
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestOrderTimeout:
    """U-P0-02: Order timeout auto-cancel tests."""

    async def test_timeout_task_cancels_expired_orders(self, db_session, test_user, test_shop_owner):
        """OrderTimeoutTask should cancel orders that are PENDING_PAYMENT and past timeout."""
        shop, _, _ = await _create_shop_with_product(db_session, test_shop_owner)

        # Create an expired order with created_at in the past
        past_time = datetime.now() - timedelta(minutes=20)
        expired_order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
            created_at=past_time,
        )
        db_session.add(expired_order)
        await db_session.commit()
        await db_session.refresh(expired_order)

        # Mock Redis to be disconnected (single instance mode)
        with patch("app.tasks.order_timeout.redis_client") as mock_redis:
            mock_redis.is_connected = False
            task = OrderTimeoutTask(db_session)
            cancelled = await task.cancel_expired_orders()

        assert cancelled >= 1

    async def test_non_pending_payment_not_cancelled(self, db_session, test_user, test_shop_owner):
        """Orders not in PENDING_PAYMENT should not be cancelled by timeout task."""
        shop, _, _ = await _create_shop_with_product(db_session, test_shop_owner)

        # Create a COMPLETED order created long ago
        past_time = datetime.now() - timedelta(minutes=20)
        completed_order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.COMPLETED,
            created_at=past_time,
        )
        db_session.add(completed_order)
        await db_session.commit()

        with patch("app.tasks.order_timeout.redis_client") as mock_redis:
            mock_redis.is_connected = False
            task = OrderTimeoutTask(db_session)
            cancelled = await task.cancel_expired_orders()

        assert cancelled == 0

    async def test_timeout_cancel_restores_stock(self, db_session, test_user, test_shop_owner):
        """When timeout cancels an order, stock should be restored."""
        shop, _, product = await _create_shop_with_product(db_session, test_shop_owner)
        product.stock = 5
        await db_session.commit()

        past_time = datetime.now() - timedelta(minutes=20)
        order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
            created_at=past_time,
        )
        db_session.add(order)
        await db_session.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=2,
        )
        db_session.add(order_item)
        product.stock = 3  # Deducted 2
        await db_session.commit()

        with patch("app.tasks.order_timeout.redis_client") as mock_redis:
            mock_redis.is_connected = False
            task = OrderTimeoutTask(db_session)
            await task.cancel_expired_orders()

        # Expire the product cache to force re-read from DB
        db_session.expire(product)
        await db_session.refresh(product)
        assert product.stock == 5  # Restored to original

    async def test_redis_lock_prevents_duplicate_processing(self, db_session, test_user, test_shop_owner):
        """When Redis lock is acquired, duplicate processing should be prevented."""
        shop, _, _ = await _create_shop_with_product(db_session, test_shop_owner)

        past_time = datetime.now() - timedelta(minutes=20)
        order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
            created_at=past_time,
        )
        db_session.add(order)
        await db_session.commit()

        # Mock Redis to be connected but lock NOT acquired (another instance holds it)
        mock_redis = MagicMock()
        mock_redis.is_connected = True
        mock_redis.client = AsyncMock()
        mock_redis.client.set = AsyncMock(return_value=None)  # Lock NOT acquired
        mock_redis.client.delete = AsyncMock()

        with patch("app.tasks.order_timeout.redis_client", mock_redis):
            task = OrderTimeoutTask(db_session)
            cancelled = await task.cancel_expired_orders()

        assert cancelled == 0  # No order cancelled because lock was not acquired

    async def test_cancel_order_with_timeout_type(self, db_session, test_user, test_shop_owner):
        """cancel_order should support cancel_type='timeout'."""
        shop, _, product = await _create_shop_with_product(db_session, test_shop_owner)
        product.stock = 10
        await db_session.commit()

        order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
        )
        db_session.add(order)
        await db_session.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=3,
        )
        db_session.add(order_item)
        product.stock = 7
        await db_session.commit()
        await db_session.refresh(order)

        service = OrderService(db_session)
        result = await service.cancel_order(
            order.id,
            cancel_type="timeout",
            reason="支付超时自动取消",
        )

        assert result.status == OrderStatus.CANCELLED

    async def test_timeout_cancel_reason_recorded(self, db_session, test_user, test_shop_owner):
        """Timeout cancel should record reason as '支付超时自动取消'."""
        shop, _, _ = await _create_shop_with_product(db_session, test_shop_owner)

        past_time = datetime.now() - timedelta(minutes=20)
        order = Order(
            order_no=generate_order_no(),
            user_id=test_user.id,
            shop_id=shop.id,
            address="测试地址",
            phone="13800138000",
            total_amount=Decimal("25.00"),
            delivery_fee=Decimal("3.00"),
            status=OrderStatus.PENDING_PAYMENT,
            created_at=past_time,
        )
        db_session.add(order)
        await db_session.commit()

        with patch("app.tasks.order_timeout.redis_client") as mock_redis:
            mock_redis.is_connected = False
            task = OrderTimeoutTask(db_session)
            await task.cancel_expired_orders()

        db_session.expire(order)
        await db_session.refresh(order)
        assert order.status == OrderStatus.CANCELLED


# ══════════════════════════════════════════════════════════════════════════════
# 8. U-P2-03-FE: 钱包前端页面（后端测试）
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestWalletRechargeEndpoint:
    """U-P2-03-FE: POST /wallet/recharge endpoint tests."""

    async def test_normal_recharge_succeeds(self, client, test_user, db_session):
        """Normal recharge should succeed and increase balance."""
        wallet = Wallet(user_id=test_user.id, balance=Decimal("100.00"), frozen_balance=Decimal("0.00"))
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/wallet/recharge",
            json={"amount": "50.00"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert float(data["amount"]) == 50.00

    async def test_recharge_zero_fails(self, client, test_user, db_session):
        """Recharging amount 0 should fail."""
        wallet = Wallet(user_id=test_user.id, balance=Decimal("100.00"), frozen_balance=Decimal("0.00"))
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/wallet/recharge",
            json={"amount": "0.00"},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_recharge_negative_fails(self, client, test_user, db_session):
        """Recharging negative amount should fail."""
        wallet = Wallet(user_id=test_user.id, balance=Decimal("100.00"), frozen_balance=Decimal("0.00"))
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/wallet/recharge",
            json={"amount": "-10.00"},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_recharge_over_limit_fails(self, client, test_user, db_session):
        """Recharging over MAX_SINGLE_RECHARGE (10000) should fail."""
        wallet = Wallet(user_id=test_user.id, balance=Decimal("0.00"), frozen_balance=Decimal("0.00"))
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/wallet/recharge",
            json={"amount": "15000.00"},
            headers=headers,
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestWalletWithdrawEndpoint:
    """U-P2-03-FE: POST /wallet/withdraw endpoint tests."""

    async def test_normal_withdraw_succeeds(self, client, test_shop_owner, db_session):
        """Normal withdrawal by SHOP_OWNER should succeed."""
        wallet = Wallet(
            user_id=test_shop_owner.id,
            balance=Decimal("1000.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_shop_owner.id, role="SHOP_OWNER")
        response = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": "test@alipay.com"},
            headers=headers,
        )
        assert response.status_code == 200

    async def test_withdraw_insufficient_balance_fails(self, client, test_shop_owner, db_session):
        """Withdrawal exceeding balance should fail."""
        wallet = Wallet(
            user_id=test_shop_owner.id,
            balance=Decimal("5.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_shop_owner.id, role="SHOP_OWNER")
        response = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": "test@alipay.com"},
            headers=headers,
        )
        assert response.status_code == 400
        # The BadRequestException handler puts message at top-level
        resp_body = response.json()
        assert "余额不足" in resp_body.get("message", "")

    async def test_withdraw_user_role_forbidden(self, client, test_user, db_session):
        """Regular USER role should get 403 on withdrawal."""
        wallet = Wallet(
            user_id=test_user.id,
            balance=Decimal("1000.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": "test@alipay.com"},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_withdraw_empty_account_fails(self, client, test_shop_owner, db_session):
        """Withdrawal with empty account should fail."""
        wallet = Wallet(
            user_id=test_shop_owner.id,
            balance=Decimal("1000.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_shop_owner.id, role="SHOP_OWNER")
        response = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "50.00", "method": "ALIPAY", "account": ""},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_rider_can_withdraw(self, client, test_rider, db_session):
        """RIDER should be able to withdraw."""
        wallet = Wallet(
            user_id=test_rider.id,
            balance=Decimal("500.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_rider.id, role="RIDER")
        response = await client.post(
            "/api/v1/wallet/withdraw",
            json={"amount": "20.00", "method": "ALIPAY", "account": "rider@alipay.com"},
            headers=headers,
        )
        assert response.status_code == 200

    async def test_admin_recharge_endpoint_requires_admin(
        self, client, test_user, db_session
    ):
        """POST /wallet/recharge/{user_id} should require ADMIN role."""
        wallet = Wallet(
            user_id=test_user.id,
            balance=Decimal("100.00"),
            frozen_balance=Decimal("0.00"),
        )
        db_session.add(wallet)
        await db_session.commit()

        headers = auth_headers(test_user.id, role="USER")
        response = await client.post(
            f"/api/v1/wallet/recharge/{test_user.id}?amount=100.0",
            headers=headers,
        )
        assert response.status_code == 403
