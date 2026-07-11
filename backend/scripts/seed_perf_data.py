"""
性能压测数据准备脚本
创建1000用户 + 100店铺 + 2000菜单 + 100骑手
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.database import engine
from app.models.models import (
    User, Wallet, Shop, Category, Product, ShopEarning,
    PlatformConfig
)
from app.models.enums import ShopStatus, ProductStatus
from app.utils.auth import hash_password


async def create_users(session: AsyncSession, count: int, role: str, phone_prefix: str):
    """批量创建用户+钱包"""
    users = []
    for i in range(count):
        phone = f"{phone_prefix}{str(i+1).zfill(8)}"
        nickname = f"{role}_{i+1}"
        user = User(
            phone=phone,
            password_hash=hash_password("Test123456"),
            nickname=nickname,
            role=role,
            status=1,
            failed_login_count=0,
        )
        users.append(user)

    session.add_all(users)
    await session.flush()

    # 批量创建钱包
    wallets = []
    for user in users:
        wallet = Wallet(user_id=user.id, balance=Decimal("1000.00"), frozen_balance=Decimal("0"))
        wallets.append(wallet)

    session.add_all(wallets)
    await session.flush()
    return users


async def create_shops(session: AsyncSession, owners: list):
    """批量创建店铺+分类+商品"""
    categories_names = ["热销推荐", "主食", "小吃", "饮品", "甜品"]
    shops = []

    for i, owner in enumerate(owners):
        shop = Shop(
            user_id=owner.id,
            name=f"店铺_{i+1:03d}",
            logo=None,
            address=f"杭州市西湖区文三路{i+1}号",
            latitude=30.2741 + random.uniform(-0.05, 0.05),
            longitude=120.1551 + random.uniform(-0.05, 0.05),
            business_hours="09:00-22:00",
            business_days="1,2,3,4,5,6,7",
            notice=f"欢迎光临店铺{i+1}！",
            rating=round(random.uniform(4.0, 5.0), 1),
            monthly_sales=random.randint(100, 2000),
            min_order_amount=Decimal(str(random.choice([10, 15, 20, 25]))),
            delivery_fee=Decimal(str(random.choice([2, 3, 5]))),
            delivery_time=f"{random.randint(15, 45)}分钟",
            discounts='["满30减5", "新用户立减3"]',
            status=ShopStatus.APPROVED.value,
        )
        shops.append(shop)

    session.add_all(shops)
    await session.flush()

    # 为每个店铺创建分类和商品
    products = []
    for shop in shops:
        shop_categories = []
        for cat_name in categories_names:
            cat = Category(
                shop_id=shop.id,
                name=cat_name,
                sort_order=categories_names.index(cat_name),
            )
            shop_categories.append(cat)

        session.add_all(shop_categories)
        await session.flush()

        # 每个分类4个商品 = 每店20个商品
        for cat in shop_categories:
            for j in range(4):
                price = round(random.uniform(8, 58), 2)
                product = Product(
                    category_id=cat.id,
                    shop_id=shop.id,
                    name=f"{cat.name}_商品{j+1}",
                    image=None,
                    price=Decimal(str(price)),
                    original_price=Decimal(str(round(price * 1.2, 2))),
                    description=f"美味{cat.name}商品{j+1}",
                    stock=random.randint(50, 500),
                    sales=random.randint(10, 300),
                    status=ProductStatus.ON.value,
                )
                products.append(product)

    session.add_all(products)
    await session.flush()
    return shops, products


async def main():
    print("=" * 60)
    print("性能压测数据准备")
    print("=" * 60)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        # 1. 创建1000个普通用户
        print("\n[1/4] 创建1000个普通用户...")
        users = await create_users(session, 1000, "USER", "150")
        print(f"  ✓ 创建完成: {len(users)} 个用户")

        # 2. 创建100个商家用户+店铺
        print("\n[2/4] 创建100个商家用户+店铺...")
        shop_owners = await create_users(session, 100, "SHOP_OWNER", "151")
        shops, products = await create_shops(session, shop_owners)
        print(f"  ✓ 创建完成: {len(shops)} 个店铺, {len(products)} 个商品")

        # 3. 创建100个骑手
        print("\n[3/4] 创建100个骑手用户...")
        riders = await create_users(session, 100, "RIDER", "152")
        print(f"  ✓ 创建完成: {len(riders)} 个骑手")

        # 4. 创建10个管理员
        print("\n[4/4] 创建10个管理员...")
        admins = await create_users(session, 10, "ADMIN", "153")
        print(f"  ✓ 创建完成: {len(admins)} 个管理员")

        # 统一提交
        await session.commit()

    # 验证数据
    print("\n" + "=" * 60)
    print("数据验证")
    print("=" * 60)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import func, text

        for table_name, model in [
            ("users", User), ("wallets", Wallet), ("shops", Shop),
            ("categories", Category), ("products", Product),
        ]:
            count = (await session.execute(select(func.count(model.id)))).scalar()
            print(f"  {table_name}: {count} 条记录")

    await engine.dispose()
    print("\n数据准备完成！所有数据已保留在OceanBase数据库中。")


if __name__ == "__main__":
    asyncio.run(main())
