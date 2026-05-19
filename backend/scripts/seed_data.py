
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from app.database import AsyncSessionLocal
from app.models.models import (
    User, Wallet, Shop, Category, Product, UserRole, ShopStatus, UserAddress
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_data():
    async with AsyncSessionLocal() as db:
        admin = User(
            phone="13800000000",
            password_hash=pwd_context.hash("admin123"),
            nickname="管理员",
            role=UserRole.ADMIN.value,
        )
        db.add(admin)
        await db.flush()

        admin_wallet = Wallet(user_id=admin.id, balance=0)
        db.add(admin_wallet)

        user = User(
            phone="13900000001",
            password_hash=pwd_context.hash("user123"),
            nickname="张三",
            role=UserRole.USER.value,
        )
        db.add(user)
        await db.flush()

        user_wallet = Wallet(user_id=user.id, balance=100)
        db.add(user_wallet)

        user_address_1 = UserAddress(
            user_id=user.id,
            contact_name="张三",
            contact_phone="13900000001",
            address="北京市朝阳区建国路88号",
            latitude=39.9088,
            longitude=116.3975,
            is_default=1,
        )
        db.add(user_address_1)

        user_address_2 = UserAddress(
            user_id=user.id,
            contact_name="张三",
            contact_phone="13900000001",
            address="北京市海淀区中关村大街1号",
            latitude=39.9890,
            longitude=116.3063,
            is_default=0,
        )
        db.add(user_address_2)

        shop_owner = User(
            phone="13900000002",
            password_hash=pwd_context.hash("shop123"),
            nickname="李老板",
            role=UserRole.SHOP_OWNER.value,
        )
        db.add(shop_owner)
        await db.flush()

        shop_wallet = Wallet(user_id=shop_owner.id, balance=0)
        db.add(shop_wallet)

        shop = Shop(
            user_id=shop_owner.id,
            name="川香楼",
            logo="https://via.placeholder.com/200x200?text=川香楼",
            address="北京市朝阳区三里屯19号",
            latitude=39.9236,
            longitude=116.4478,
            business_hours="09:00-22:00",
            notice="欢迎光临川香楼，正宗川菜等你来尝！",
            status=ShopStatus.APPROVED.value,
            rating=4.8,
        )
        db.add(shop)
        await db.flush()

        category_1 = Category(shop_id=shop.id, name="招牌菜", sort_order=1)
        category_2 = Category(shop_id=shop.id, name="凉菜", sort_order=2)
        category_3 = Category(shop_id=shop.id, name="主食", sort_order=3)
        db.add_all([category_1, category_2, category_3])
        await db.flush()

        products = [
            Product(
                shop_id=shop.id, category_id=category_1.id,
                name="麻婆豆腐", price=38.0, stock=100,
                image="https://via.placeholder.com/200x200?text=麻婆豆腐",
                description="正宗川味麻辣豆腐，下饭神器",
                sales=520,
            ),
            Product(
                shop_id=shop.id, category_id=category_1.id,
                name="宫保鸡丁", price=42.0, stock=80,
                image="https://via.placeholder.com/200x200?text=宫保鸡丁",
                description="经典川菜，鸡丁香嫩，花生酥脆",
                sales=480,
            ),
            Product(
                shop_id=shop.id, category_id=category_1.id,
                name="水煮鱼", price=88.0, stock=30,
                image="https://via.placeholder.com/200x200?text=水煮鱼",
                description="新鲜草鱼，麻辣鲜香",
                sales=280,
            ),
            Product(
                shop_id=shop.id, category_id=category_2.id,
                name="凉拌黄瓜", price=18.0, stock=200,
                image="https://via.placeholder.com/200x200?text=凉拌黄瓜",
                description="清脆爽口，开胃小菜",
                sales=350,
            ),
            Product(
                shop_id=shop.id, category_id=category_2.id,
                name="夫妻肺片", price=48.0, stock=50,
                image="https://via.placeholder.com/200x200?text=夫妻肺片",
                description="麻辣鲜香，经典凉菜",
                sales=220,
            ),
            Product(
                shop_id=shop.id, category_id=category_3.id,
                name="白米饭", price=3.0, stock=500,
                image="https://via.placeholder.com/200x200?text=米饭",
                description="东北大米，香软可口",
                sales=1000,
            ),
        ]
        db.add_all(products)

        shop2 = Shop(
            user_id=shop_owner.id,
            name="粤式茶餐厅",
            logo="https://via.placeholder.com/200x200?text=粤式茶餐厅",
            address="北京市朝阳区工体北路",
            latitude=39.9325,
            longitude=116.4431,
            business_hours="08:00-21:00",
            notice="粤式风味，精致点心",
            status=ShopStatus.APPROVED.value,
            rating=4.6,
        )
        db.add(shop2)
        await db.flush()

        cat_yue = Category(shop_id=shop2.id, name="早点", sort_order=1)
        db.add(cat_yue)
        await db.flush()

        products_yue = [
            Product(
                shop_id=shop2.id, category_id=cat_yue.id,
                name="虾饺", price=32.0, stock=60,
                image="https://via.placeholder.com/200x200?text=虾饺",
                description="新鲜虾仁，皮薄馅大",
                sales=300,
            ),
            Product(
                shop_id=shop2.id, category_id=cat_yue.id,
                name="叉烧包", price=22.0, stock=80,
                image="https://via.placeholder.com/200x200?text=叉烧包",
                description="秘制叉烧馅，松软可口",
                sales=400,
            ),
        ]
        db.add_all(products_yue)

        rider = User(
            phone="13900000003",
            password_hash=pwd_context.hash("rider123"),
            nickname="王师傅",
            role=UserRole.RIDER.value,
        )
        db.add(rider)
        await db.flush()

        rider_wallet = Wallet(user_id=rider.id, balance=50)
        db.add(rider_wallet)

        await db.commit()
        print("Seed data created successfully!")
        print("\n=== Test Accounts ===")
        print("Admin: 13800000000 / admin123")
        print("User: 13900000001 / user123")
        print("Shop Owner: 13900000002 / shop123")
        print("Rider: 13900000003 / rider123")


if __name__ == "__main__":
    asyncio.run(seed_data())

