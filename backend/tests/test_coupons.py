import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.models.models import Coupon, UserCoupon


@pytest.mark.asyncio
class TestCouponsAPI:
    async def test_list_available_coupons(self, client: AsyncClient, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="TESTCOUPON001",
            name="测试优惠券",
            description="满50减10",
            discount_amount=10.0,
            min_order_amount=50.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()

        response = await client.get("/api/v1/coupons")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) > 0
        assert data["data"]["total"] >= 1

    async def test_list_available_coupons_excludes_expired(self, client: AsyncClient, db_session: AsyncSession):
        now = datetime.now()
        expired_coupon = Coupon(
            code="EXPIREDCOUPON",
            name="已过期优惠券",
            discount_amount=5.0,
            min_order_amount=20.0,
            total_count=50,
            remain_count=10,
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=1),
            status="ACTIVE",
        )
        db_session.add(expired_coupon)
        await db_session.commit()

        response = await client.get("/api/v1/coupons")
        assert response.status_code == 200
        data = response.json()
        coupon_codes = [c["code"] for c in data["data"]["items"]]
        assert "EXPIREDCOUPON" not in coupon_codes

    async def test_list_available_coupons_excludes_used_up(self, client: AsyncClient, db_session: AsyncSession):
        now = datetime.now()
        used_up_coupon = Coupon(
            code="USEDUPCOUPON",
            name="已领完优惠券",
            discount_amount=8.0,
            min_order_amount=30.0,
            total_count=100,
            remain_count=0,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(used_up_coupon)
        await db_session.commit()

        response = await client.get("/api/v1/coupons")
        assert response.status_code == 200
        data = response.json()
        coupon_codes = [c["code"] for c in data["data"]["items"]]
        assert "USEDUPCOUPON" not in coupon_codes

    async def test_claim_coupon(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="CLAIMABLE001",
            name="可领取优惠券",
            discount_amount=15.0,
            min_order_amount=60.0,
            total_count=200,
            remain_count=100,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        initial_remain_count = coupon.remain_count

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/coupons/{coupon.id}/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "领取成功"
        assert data["data"]["coupon_id"] == coupon.id
        assert data["data"]["status"] == "UNUSED"

        await db_session.refresh(coupon)
        assert coupon.remain_count == initial_remain_count - 1

    async def test_claim_coupon_not_found(self, client: AsyncClient, test_user):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/coupons/99999/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    async def test_claim_coupon_already_claimed(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="ALREADYCLAIMED",
            name="已领取优惠券",
            discount_amount=12.0,
            min_order_amount=40.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="UNUSED"
        )
        db_session.add(user_coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/coupons/{coupon.id}/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "您已领取过该优惠券"

    async def test_claim_coupon_expired(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="EXPIREDCLAIM",
            name="过期优惠券",
            discount_amount=20.0,
            min_order_amount=100.0,
            total_count=50,
            remain_count=20,
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=1),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/coupons/{coupon.id}/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "优惠券已过期"

    async def test_claim_coupon_not_started(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="NOTSTARTED",
            name="未开始优惠券",
            discount_amount=25.0,
            min_order_amount=80.0,
            total_count=100,
            remain_count=50,
            valid_from=now + timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/coupons/{coupon.id}/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "优惠券还未开始"

    async def test_claim_coupon_used_up(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="USAGEDUPOUT",
            name="领完优惠券",
            discount_amount=10.0,
            min_order_amount=30.0,
            total_count=10,
            remain_count=0,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/coupons/{coupon.id}/claim",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "优惠券已领完"


@pytest.mark.asyncio
class TestMyCouponsAPI:
    async def test_list_my_coupons(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="MYCOUPON001",
            name="我的优惠券1",
            discount_amount=10.0,
            min_order_amount=50.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="UNUSED"
        )
        db_session.add(user_coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/coupons/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) >= 1

    async def test_list_my_coupons_filter_unused(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon1 = Coupon(
            code="FILTERUNUSED1",
            name="未使用优惠券",
            discount_amount=10.0,
            min_order_amount=30.0,
            total_count=50,
            remain_count=30,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon1)
        await db_session.commit()
        await db_session.refresh(coupon1)

        coupon2 = Coupon(
            code="FILTERUSED1",
            name="已使用优惠券",
            discount_amount=15.0,
            min_order_amount=50.0,
            total_count=50,
            remain_count=30,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon2)
        await db_session.commit()
        await db_session.refresh(coupon2)

        user_coupon1 = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon1.id,
            status="UNUSED"
        )
        user_coupon2 = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon2.id,
            status="USED"
        )
        db_session.add(user_coupon1)
        db_session.add(user_coupon2)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/coupons/my?status=UNUSED",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]["items"]:
            assert item["status"] == "UNUSED"

    async def test_list_my_coupons_filter_used(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="FILTERUSEDCOUPON",
            name="已使用筛选测试",
            discount_amount=20.0,
            min_order_amount=80.0,
            total_count=50,
            remain_count=30,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="USED"
        )
        db_session.add(user_coupon)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/coupons/my?status=USED",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]["items"]:
            assert item["status"] == "USED"


@pytest.mark.asyncio
class TestApplyCouponAPI:
    async def test_apply_coupon_success(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="APPLYCOUPON",
            name="应用测试优惠券",
            discount_amount=10.0,
            min_order_amount=50.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        # 用户先领取优惠券
        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="UNUSED",
        )
        db_session.add(user_coupon)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/coupons/apply?coupon_id={coupon.id}&order_amount=80.0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "优惠券可用"
        assert data["data"]["discount_amount"] == 10.0
        assert data["data"]["final_amount"] == 70.0

    async def test_apply_coupon_min_amount_not_met(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="MINAMOUNTCOUPON",
            name="最低消费优惠券",
            discount_amount=10.0,
            min_order_amount=100.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        # 用户先领取优惠券
        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="UNUSED",
        )
        db_session.add(user_coupon)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/coupons/apply?coupon_id={coupon.id}&order_amount=50.0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "订单金额需满" in response.json()["message"]

    async def test_apply_coupon_not_found(self, client: AsyncClient, test_user):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/coupons/apply?coupon_id=99999&order_amount=100.0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    async def test_apply_coupon_discount_capped_by_amount(self, client: AsyncClient, test_user, db_session: AsyncSession):
        now = datetime.now()
        coupon = Coupon(
            code="MAXDISCOUNTOK",
            name="最大折扣测试",
            discount_amount=50.0,
            min_order_amount=20.0,
            total_count=100,
            remain_count=50,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            status="ACTIVE",
        )
        db_session.add(coupon)
        await db_session.commit()
        await db_session.refresh(coupon)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        # 用户先领取优惠券
        user_coupon = UserCoupon(
            user_id=test_user.id,
            coupon_id=coupon.id,
            status="UNUSED",
        )
        db_session.add(user_coupon)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/coupons/apply?coupon_id={coupon.id}&order_amount=30.0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["discount_amount"] == 30.0
        assert data["data"]["final_amount"] == 0.0


@pytest.mark.asyncio
class TestCouponAuthRequired:
    async def test_claim_coupon_requires_auth(self, client: AsyncClient):
        response = await client.post("/api/v1/coupons/1/claim")
        assert response.status_code == 401

    async def test_my_coupons_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/coupons/my")
        assert response.status_code == 401

    async def test_apply_coupon_requires_auth(self, client: AsyncClient):
        response = await client.post("/api/v1/coupons/apply", json={
            "coupon_id": 1,
            "order_amount": 100.0
        })
        assert response.status_code == 401
