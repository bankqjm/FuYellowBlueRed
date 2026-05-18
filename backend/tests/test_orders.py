import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import (
    User, UserRole, UserStatus, 
    Shop, Category, Product, ProductStatus,
    UserAddress, CartItem, Order, OrderStatus
)
from app.utils.auth import hash_password


@pytest.mark.asyncio
class TestCartAPI:
    async def test_add_to_cart(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139001",
            password_hash=hash_password("Test123456"),
            nickname="测试商家",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

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
            price=25.0,
            stock=100,
            status=ProductStatus.ON.value,
        )
        db_session.add(product)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/orders/cart",
            json={
                "shop_id": shop.id,
                "product_id": product.id,
                "quantity": 2
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["quantity"] == 2
        assert data["data"]["product_name"] == "测试商品"

    async def test_add_to_cart_product_not_found(self, client: AsyncClient, test_user, db_session: AsyncSession):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/orders/cart",
            json={
                "shop_id": 99999,
                "product_id": 99999,
                "quantity": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "商品不存在或已下架"

    async def test_get_cart(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139002",
            password_hash=hash_password("Test123456"),
            nickname="测试商家2",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺2",
            address="测试地址2",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        product = Product(
            shop_id=shop.id,
            name="测试商品2",
            price=30.0,
            stock=50,
            status=ProductStatus.ON.value,
        )
        db_session.add(product)
        await db_session.commit()

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=3
        )
        db_session.add(cart_item)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/orders/cart",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) > 0

    async def test_update_cart_item(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139003",
            password_hash=hash_password("Test123456"),
            nickname="测试商家3",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺3",
            address="测试地址3",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        product = Product(
            shop_id=shop.id,
            name="测试商品3",
            price=15.0,
            stock=20,
            status=ProductStatus.ON.value,
        )
        db_session.add(product)
        await db_session.commit()

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=1
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.put(
            f"/api/v1/orders/cart/{cart_item.id}",
            json={"quantity": 5},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["quantity"] == 5

    async def test_delete_cart_item(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139004",
            password_hash=hash_password("Test123456"),
            nickname="测试商家4",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺4",
            address="测试地址4",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        product = Product(
            shop_id=shop.id,
            name="测试商品4",
            price=20.0,
            stock=30,
            status=ProductStatus.ON.value,
        )
        db_session.add(product)
        await db_session.commit()

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=1
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.delete(
            f"/api/v1/orders/cart/{cart_item.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


@pytest.mark.asyncio
class TestOrderAPI:
    async def test_create_order(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139005",
            password_hash=hash_password("Test123456"),
            nickname="测试商家5",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺5",
            address="测试地址5",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        product = Product(
            shop_id=shop.id,
            name="测试商品5",
            price=50.0,
            stock=10,
            status=ProductStatus.ON.value,
        )
        db_session.add(product)
        await db_session.commit()

        cart_item = CartItem(
            user_id=test_user.id,
            shop_id=shop.id,
            product_id=product.id,
            quantity=2
        )
        db_session.add(cart_item)
        await db_session.commit()

        address = UserAddress(
            user_id=test_user.id,
            contact_name="张三",
            contact_phone="13800138000",
            address="测试收货地址",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/orders/create",
            json={
                "address_id": address.id,
                "shop_id": shop.id,
                "remark": "测试备注"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == OrderStatus.PENDING_PAYMENT.value
        assert "order_no" in data["data"]

    async def test_create_order_empty_cart(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139006",
            password_hash=hash_password("Test123456"),
            nickname="测试商家6",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺6",
            address="测试地址6",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="李四",
            contact_phone="13800138000",
            address="测试收货地址2",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/orders/create",
            json={
                "address_id": address.id,
                "shop_id": shop.id,
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "购物车为空"

    async def test_create_order_address_not_found(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139007",
            password_hash=hash_password("Test123456"),
            nickname="测试商家7",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺7",
            address="测试地址7",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/orders/create",
            json={
                "address_id": 99999,
                "shop_id": shop.id,
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "收货地址不存在"

    async def test_list_orders(self, client: AsyncClient, test_user, db_session: AsyncSession):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]

    async def test_get_order_detail(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139008",
            password_hash=hash_password("Test123456"),
            nickname="测试商家8",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺8",
            address="测试地址8",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="王五",
            contact_phone="13800138000",
            address="测试收货地址3",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        order = Order(
            order_no="TESTORDER12345678901234",
            user_id=test_user.id,
            shop_id=shop.id,
            address=address.address,
            phone=address.contact_phone,
            total_amount=30.0,
            delivery_fee=5.0,
            status=OrderStatus.PENDING_PAYMENT.value,
        )
        db_session.add(order)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            f"/api/v1/orders/{order.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == order.id

    async def test_get_order_detail_not_found(self, client: AsyncClient, test_user):
        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/orders/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "订单不存在"


@pytest.mark.asyncio
class TestOrderCancel:
    async def test_cancel_order_pending_payment(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139009",
            password_hash=hash_password("Test123456"),
            nickname="测试商家9",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺9",
            address="测试地址9",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="赵六",
            contact_phone="13800138000",
            address="测试收货地址4",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        order = Order(
            order_no="CANCELTEST1234567890123",
            user_id=test_user.id,
            shop_id=shop.id,
            address=address.address,
            phone=address.contact_phone,
            total_amount=25.0,
            delivery_fee=5.0,
            status=OrderStatus.PENDING_PAYMENT.value,
        )
        db_session.add(order)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.put(
            f"/api/v1/orders/{order.id}/cancel",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == OrderStatus.CANCELLED.value

    async def test_cancel_order_cannot_cancel_completed(self, client: AsyncClient, test_user, db_session: AsyncSession):
        shop_owner = User(
            phone="13900139010",
            password_hash=hash_password("Test123456"),
            nickname="测试商家10",
            role=UserRole.SHOP_OWNER.value,
            status=UserStatus.ACTIVE.value,
        )
        db_session.add(shop_owner)
        await db_session.commit()
        await db_session.refresh(shop_owner)

        shop = Shop(
            user_id=shop_owner.id,
            name="测试店铺10",
            address="测试地址10",
            status=1,
        )
        db_session.add(shop)
        await db_session.commit()
        await db_session.refresh(shop)

        address = UserAddress(
            user_id=test_user.id,
            contact_name="钱七",
            contact_phone="13800138000",
            address="测试收货地址5",
            is_default=1,
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        order = Order(
            order_no="COMPLTED123456789012345",
            user_id=test_user.id,
            shop_id=shop.id,
            address=address.address,
            phone=address.contact_phone,
            total_amount=35.0,
            delivery_fee=5.0,
            status=OrderStatus.COMPLETED.value,
        )
        db_session.add(order)
        await db_session.commit()

        login_response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        token = login_response.json()["data"]["access_token"]

        response = await client.put(
            f"/api/v1/orders/{order.id}/cancel",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["message"] == "当前订单状态不可取消"
