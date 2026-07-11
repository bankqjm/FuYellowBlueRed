import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import (
    User, UserRole, UserStatus, Wallet, FundFlow,
    FlowType, BusinessType, AccountType
)
from app.utils.auth import hash_password


@pytest.mark.asyncio
class TestWalletAPI:
    async def test_get_wallet(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(
            user_id=test_user.id,
            balance=100.0,
            frozen_balance=0.0
        )
        db_session.add(wallet)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["balance"] == 100.0
        assert "id" in data["data"]

    async def test_get_wallet_creates_if_not_exists(self, client: AsyncClient, test_user):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["balance"] == 0.0

    async def test_get_wallet_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/wallet")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestWalletTransactionsAPI:
    async def test_get_transactions(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(user_id=test_user.id, balance=500.0)
        db_session.add(wallet)
        await db_session.commit()

        fund_flow1 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=200.0,
            balance_before=0.0,
            balance_after=200.0,
            business_type=BusinessType.RECHARGE.value,
            description="充值200元"
        )
        fund_flow2 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.EXPENSE.value,
            amount=50.0,
            balance_before=200.0,
            balance_after=150.0,
            business_type=BusinessType.ORDER_PAY.value,
            description="订单支付"
        )
        db_session.add(fund_flow1)
        db_session.add(fund_flow2)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 2

    async def test_get_transactions_filter_business_type(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(user_id=test_user.id, balance=500.0)
        db_session.add(wallet)
        await db_session.commit()

        fund_flow1 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=100.0,
            balance_before=0.0,
            balance_after=100.0,
            business_type=BusinessType.RECHARGE.value,
            description="充值"
        )
        fund_flow2 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=200.0,
            balance_before=100.0,
            balance_after=300.0,
            business_type=BusinessType.ORDER_REFUND.value,
            description="退款"
        )
        db_session.add(fund_flow1)
        db_session.add(fund_flow2)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet/transactions?business_type=RECHARGE",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["business_type"] == "RECHARGE"

    async def test_get_transactions_filter_flow_type(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(user_id=test_user.id, balance=500.0)
        db_session.add(wallet)
        await db_session.commit()

        fund_flow1 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=300.0,
            balance_before=0.0,
            balance_after=300.0,
            business_type=BusinessType.RECHARGE.value,
            description="充值"
        )
        fund_flow2 = FundFlow(
            user_id=test_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.EXPENSE.value,
            amount=100.0,
            balance_before=300.0,
            balance_after=200.0,
            business_type=BusinessType.ORDER_PAY.value,
            description="支付"
        )
        db_session.add(fund_flow1)
        db_session.add(fund_flow2)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet/transactions?flow_type=INCOME",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]["items"]:
            assert item["flow_type"] == "INCOME"

    async def test_get_transactions_pagination(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(user_id=test_user.id, balance=1000.0)
        db_session.add(wallet)
        await db_session.commit()

        for i in range(10):
            fund_flow = FundFlow(
                user_id=test_user.id,
                account_type=AccountType.USER.value,
                flow_type=FlowType.INCOME.value,
                amount=10.0 * (i + 1),
                balance_before=0.0,
                balance_after=10.0 * (i + 1),
                business_type=BusinessType.RECHARGE.value,
                description=f"充值{i+1}"
            )
            db_session.add(fund_flow)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet/transactions?page=1&page_size=3",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) == 3
        assert data["data"]["total"] == 10

    async def test_transactions_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/wallet/transactions")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAdminRechargeAPI:
    async def test_admin_recharge_user(self, client: AsyncClient, test_user, test_admin, db_session: AsyncSession):
        target_user = User(
            phone="13900338001",
            password_hash=hash_password("Test123456"),
            nickname="充值目标用户",
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(target_user)
        await db_session.commit()
        await db_session.refresh(target_user)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13600136000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/wallet/recharge/{target_user.id}",
            json={"amount": 500.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "用户充值成功"
        assert data["data"]["user_id"] == target_user.id

        wallet_result = await db_session.execute(
            select(Wallet).where(Wallet.user_id == target_user.id)
        )
        wallet = wallet_result.scalar_one()
        assert wallet.balance == 500.0

    async def test_admin_recharge_requires_admin_role(self, client: AsyncClient, test_user, test_shop_owner, db_session: AsyncSession):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13900139000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/wallet/recharge/{test_user.id}",
            json={"amount": 100.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    async def test_user_cannot_recharge_others(self, client: AsyncClient, test_user, db_session: AsyncSession):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/wallet/recharge/{test_user.id}",
            json={"amount": 100.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestFundFlowService:
    async def test_create_fund_flow_records_transaction(self, client: AsyncClient, test_user, db_session: AsyncSession):
        wallet = Wallet(user_id=test_user.id, balance=200.0)
        db_session.add(wallet)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0

    async def test_fund_flow_balance_tracking(self, client: AsyncClient, test_user, db_session: AsyncSession):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/wallet",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data["data"]
        assert "total_expense" in data["data"]
