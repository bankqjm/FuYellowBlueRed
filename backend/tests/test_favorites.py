import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.models import User, UserRole, UserStatus, Shop, Favorite
from app.utils.auth import hash_password


@pytest.mark.asyncio
class TestFavoritesAPI:
    async def test_add_favorite(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239001",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家1",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺1",
            address="收藏测试地址1",
            rating=4.8,
            monthly_sales=500,
            delivery_time="25分钟",
            min_order_amount=15.0,
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/favorites/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "收藏成功"
        assert data["data"]["shop_id"] == shop.id

    async def test_add_favorite_shop_not_found(self, client: AsyncClient, test_user):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/favorites/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    async def test_add_favorite_already_exists(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239002",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家2",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺2",
            address="收藏测试地址2",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        favorite = Favorite(user_id=test_user.id, shop_id=shop.id)
        db_session.add(favorite)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/favorites/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "已收藏过该店铺"

    async def test_list_favorites(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner1 = User(
            phone="13900239003",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家3",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner1)
        await db_session.commit()
        await db_session.refresh(shop_owner1)

        shop1 = Shop(
            user_id=shop_owner1.id,
            name="收藏测试店铺3",
            address="收藏测试地址3",
            rating=4.5,
            monthly_sales=100,
            delivery_time="30分钟",
            status=1,
        )
        db_session.add(shop1)
        await db_session.commit()
        await db_session.refresh(shop1)

        shop_owner2 = User(
            phone="13900239004",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家4",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner2)
        await db_session.commit()
        await db_session.refresh(shop_owner2)

        shop2 = Shop(
            user_id=shop_owner2.id,
            name="收藏测试店铺4",
            address="收藏测试地址4",
            rating=4.9,
            monthly_sales=200,
            delivery_time="20分钟",
            status=1,
        )
        db_session.add(shop2)
        await db_session.commit()

        favorite1 = Favorite(user_id=test_user.id, shop_id=shop1.id)
        favorite2 = Favorite(user_id=test_user.id, shop_id=shop2.id)
        db_session.add(favorite1)
        db_session.add(favorite2)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 2

    async def test_list_favorites_pagination(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239005",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家5",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        for i in range(5):
            shop = Shop(
                user_id=shop_owner.id,
                name=f"分页测试店铺{i+1}",
                address=f"分页测试地址{i+1}",
                status=1,
            )
            db_session.add(shop)
            await db_session.commit()
            await db_session.refresh(shop)

            favorite = Favorite(user_id=test_user.id, shop_id=shop.id)
            db_session.add(favorite)
            await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/favorites?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 5

    async def test_remove_favorite(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239006",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家6",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺6",
            address="收藏测试地址6",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        favorite = Favorite(user_id=test_user.id, shop_id=shop.id)
        db_session.add(favorite)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.delete(
            f"/api/v1/favorites/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "取消收藏成功"

    async def test_remove_favorite_not_exists(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239007",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家7",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺7",
            address="收藏测试地址7",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.delete(
            f"/api/v1/favorites/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert response.json()["message"] == "收藏记录不存在"

    async def test_check_favorite(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239008",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家8",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺8",
            address="收藏测试地址8",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        favorite = Favorite(user_id=test_user.id, shop_id=shop.id)
        db_session.add(favorite)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            f"/api/v1/favorites/check/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_favorited"] == True

    async def test_check_favorite_not_favorited(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900239009",
            password_hash=hash_password("Test123456"),
            nickname="收藏测试商家9",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="收藏测试店铺9",
            address="收藏测试地址9",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            f"/api/v1/favorites/check/{shop.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_favorited"] == False

    async def test_favorites_require_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/favorites")
        assert response.status_code == 401

    async def test_add_favorite_require_auth(self, client: AsyncClient):
        response = await client.post("/api/v1/favorites/1")
        assert response.status_code == 401

    async def test_remove_favorite_require_auth(self, client: AsyncClient):
        response = await client.delete("/api/v1/favorites/1")
        assert response.status_code == 401
