import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import (
    User, Shop, Wallet, AuditLog, FinanceAuditLog, ShopEarning, SettlementStatus,
)
from app.utils.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_cycle3.db"

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
async def test_f1_audit_logs_api_admin_only(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000001")
    user = await create_test_user(db, role="USER", phone="19900000002")

    admin_headers = auth_headers(admin.id, role="ADMIN")
    user_headers = auth_headers(user.id, role="USER")

    res_user = await client.get("/api/v1/audit/logs", headers=user_headers)
    assert res_user.status_code in (401, 403)

    res_admin = await client.get("/api/v1/audit/logs", headers=admin_headers)
    assert res_admin.status_code == 200
    assert "items" in res_admin.json()["data"]


@pytest.mark.asyncio
async def test_f1_audit_logs_with_data(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000003")
    headers = auth_headers(admin.id, role="ADMIN")

    log = AuditLog(
        user_id=admin.id,
        action="LOGIN",
        resource="user",
        resource_id=str(admin.id),
        details="User logged in",
        ip_address="127.0.0.1",
    )
    db.add(log)
    await db.commit()

    res = await client.get("/api/v1/audit/logs", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "LOGIN"


@pytest.mark.asyncio
async def test_f1_audit_logs_filter_by_action(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000004")
    headers = auth_headers(admin.id, role="ADMIN")

    db.add(AuditLog(user_id=admin.id, action="LOGIN", resource="user"))
    db.add(AuditLog(user_id=admin.id, action="LOGOUT", resource="user"))
    await db.commit()

    res = await client.get("/api/v1/audit/logs?action=LOGIN", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert all(item["action"] == "LOGIN" for item in data["items"])


@pytest.mark.asyncio
async def test_f1_finance_audit_logs(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000005")
    headers = auth_headers(admin.id, role="ADMIN")

    db.add(FinanceAuditLog(
        user_id=admin.id,
        audit_type="WITHDRAWAL",
        amount=100.0,
        description="Rider withdrawal",
        is_alert=0,
    ))
    await db.commit()

    res = await client.get("/api/v1/audit/finance", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["audit_type"] == "WITHDRAWAL"


@pytest.mark.asyncio
async def test_f1_finance_audit_logs_filter_alert(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000006")
    headers = auth_headers(admin.id, role="ADMIN")

    db.add(FinanceAuditLog(user_id=admin.id, audit_type="REFUND", amount=50.0, is_alert=1))
    db.add(FinanceAuditLog(user_id=admin.id, audit_type="WITHDRAWAL", amount=100.0, is_alert=0))
    await db.commit()

    res = await client.get("/api/v1/audit/finance?is_alert=1", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert all(item["is_alert"] == 1 for item in data["items"])


@pytest.mark.asyncio
async def test_f2_config_api_admin_only(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000007")
    user = await create_test_user(db, role="USER", phone="19900000008")

    user_headers = auth_headers(user.id, role="USER")
    admin_headers = auth_headers(admin.id, role="ADMIN")

    res_user = await client.get("/api/v1/admin/config", headers=user_headers)
    assert res_user.status_code == 403

    res_admin = await client.get("/api/v1/admin/config", headers=admin_headers)
    assert res_admin.status_code == 200


@pytest.mark.asyncio
async def test_f2_config_get_all_returns_defaults(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000009")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.get("/api/v1/admin/config", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "configs" in data
    assert "defaults" in data
    config_keys = [c["key"] for c in data["configs"]]
    assert "SHOP_COMMISSION_RATE" in config_keys


@pytest.mark.asyncio
async def test_f2_config_get_single(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000010")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.get("/api/v1/admin/config/SHOP_COMMISSION_RATE", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["key"] == "SHOP_COMMISSION_RATE"
    assert data["value"] == "0.10"


@pytest.mark.asyncio
async def test_f2_config_update(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000011")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.put(
        "/api/v1/admin/config/PLATFORM_NAME",
        json={"value": "TestPlatform"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["value"] == "TestPlatform"

    get_res = await client.get("/api/v1/admin/config/PLATFORM_NAME", headers=headers)
    assert get_res.json()["data"]["value"] == "TestPlatform"


@pytest.mark.asyncio
async def test_f2_config_update_rate_validation(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000012")
    headers = auth_headers(admin.id, role="ADMIN")

    res_bad = await client.put(
        "/api/v1/admin/config/SHOP_COMMISSION_RATE",
        json={"value": "2.0"},
        headers=headers,
    )
    assert res_bad.status_code == 400

    res_good = await client.put(
        "/api/v1/admin/config/SHOP_COMMISSION_RATE",
        json={"value": "0.15"},
        headers=headers,
    )
    assert res_good.status_code == 200
    assert res_good.json()["data"]["value"] == "0.15"


@pytest.mark.asyncio
async def test_f2_config_invalid_key(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000013")
    headers = auth_headers(admin.id, role="ADMIN")

    res = await client.put(
        "/api/v1/admin/config/INVALID_KEY",
        json={"value": "test"},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_f3_earnings_summary_shop_owner_only(db, client):
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="19900000014")
    user = await create_test_user(db, role="USER", phone="19900000015")

    shop = Shop(
        user_id=shop_owner.id,
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

    user_headers = auth_headers(user.id, role="USER")
    owner_headers = auth_headers(shop_owner.id, role="SHOP_OWNER")

    res_user = await client.get("/api/v1/shop/earnings/summary", headers=user_headers)
    assert res_user.status_code == 403

    res_owner = await client.get("/api/v1/shop/earnings/summary", headers=owner_headers)
    assert res_owner.status_code == 200
    data = res_owner.json()["data"]
    assert "total_earnings" in data
    assert "settled_amount" in data
    assert "unsettled_amount" in data
    assert "order_count" in data


@pytest.mark.asyncio
async def test_f3_earnings_list(db, client):
    shop_owner = await create_test_user(db, role="SHOP_OWNER", phone="19900000016")
    shop = Shop(
        user_id=shop_owner.id,
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

    earning = ShopEarning(
        shop_id=shop.id,
        order_id=1,
        order_no="ORD001",
        goods_amount=100.0,
        commission_rate=0.10,
        commission_amount=10.0,
        net_amount=90.0,
        status=SettlementStatus.UNSETTLED.value,
    )
    db.add(earning)
    await db.commit()

    headers = auth_headers(shop_owner.id, role="SHOP_OWNER")
    res = await client.get("/api/v1/shop/earnings/list", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["net_amount"] == 90.0


@pytest.mark.asyncio
async def test_f3_commission_summary_admin_only(db, client):
    admin = await create_test_user(db, role="ADMIN", phone="19900000017")
    user = await create_test_user(db, role="USER", phone="19900000018")

    user_headers = auth_headers(user.id, role="USER")
    admin_headers = auth_headers(admin.id, role="ADMIN")

    res_user = await client.get("/api/v1/shop/earnings/commission/summary", headers=user_headers)
    assert res_user.status_code == 403

    res_admin = await client.get("/api/v1/shop/earnings/commission/summary", headers=admin_headers)
    assert res_admin.status_code == 200


@pytest.mark.asyncio
async def test_f4_login_sets_httponly_cookie(db, client):
    await create_test_user(db, role="USER", phone="19900000019")

    res = await client.post("/api/v1/auth/login", json={
        "phone": "19900000019",
        "password": "TestPass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_f4_logout_clears_cookie(db, client):
    await create_test_user(db, role="USER", phone="19900000020")

    login_res = await client.post("/api/v1/auth/login", json={
        "phone": "19900000020",
        "password": "TestPass123",
    })
    assert login_res.status_code == 200

    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_f4_login_lockout(db, client):
    await create_test_user(db, role="USER", phone="19900000021")

    for i in range(5):
        res = await client.post("/api/v1/auth/login", json={
            "phone": "19900000021",
            "password": "WrongPassword",
        })
        assert res.status_code == 400

    lock_res = await client.post("/api/v1/auth/login", json={
        "phone": "19900000021",
        "password": "TestPass123",
    })
    assert lock_res.status_code == 400
    assert "锁定" in lock_res.json()["message"]


@pytest.mark.asyncio
async def test_f5_security_headers(db, client):
    user = await create_test_user(db, role="USER", phone="19900000022")
    headers = auth_headers(user.id, role="USER")

    res = await client.get("/api/v1/auth/login", headers=headers)
    assert "x-content-type-options" in res.headers
    assert res.headers["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in res.headers
    assert res.headers["x-frame-options"] == "DENY"
    assert "x-xss-protection" in res.headers
    assert "referrer-policy" in res.headers
    assert "content-security-policy" in res.headers
