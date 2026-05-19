
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import (
    Shop, Category, Product, ShopStatus, ProductStatus, User, Order, OrderItem, OrderStatus,
)
from app.schemas.shop import (
    ShopCreate, ShopUpdate, ShopInfo, ShopDetail,
    CategoryCreate, CategoryUpdate, CategoryInfo,
    ProductCreate, ProductUpdate, ProductInfo,
    ShopListQuery, ProductListQuery,
)
from app.schemas.order import OrderResponse, OrderItemResponse, OrderQuery, AddressInfo
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, ForbiddenException, get_logger

router = APIRouter(prefix="/shop", tags=["商家"])
logger = get_logger("shop")


@router.post("/apply", response_model=ResponseSchema[ShopInfo])
async def apply_shop(
    request: ShopCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_shop = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    if existing_shop.scalar_one_or_none():
        raise BadRequestException("您已申请过店铺")

    shop = Shop(
        user_id=current_user.id,
        name=request.name,
        logo=request.logo,
        address=request.address,
        latitude=request.latitude,
        longitude=request.longitude,
        business_hours=request.business_hours,
        notice=request.notice,
        status=ShopStatus.PENDING.value,
        rating=5.0
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    logger.info(f"Shop applied: {shop.id} by user {current_user.id}")

    return ResponseSchema(
        code=0,
        message="申请成功，等待审核",
        data=ShopInfo.model_validate(shop)
    )


@router.get("/my", response_model=ResponseSchema[ShopInfo])
async def get_my_shop(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有申请店铺")
    return ResponseSchema(code=0, data=ShopInfo.model_validate(shop))


@router.put("/my", response_model=ResponseSchema[ShopInfo])
async def update_my_shop(
    request: ShopUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有申请店铺")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shop, field, value)

    await db.commit()
    await db.refresh(shop)
    return ResponseSchema(code=0, message="更新成功", data=ShopInfo.model_validate(shop))


@router.get("/categories", response_model=ResponseSchema[list[CategoryInfo]])
async def list_all_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()

    category_list = []
    for cat in categories:
        products_result = await db.execute(
            select(Product).where(Product.category_id == cat.id, Product.status == ProductStatus.ON.value)
        )
        products = products_result.scalars().all()

        cat_data = CategoryInfo(
            id=cat.id,
            shop_id=cat.shop_id,
            name=cat.name,
            sort_order=cat.sort_order,
            created_at=cat.created_at,
            products=[ProductInfo.model_validate(p) for p in products]
        )
        category_list.append(cat_data)

    return ResponseSchema(code=0, data=category_list)


@router.get("/list", response_model=ResponseSchema[PageResponse[ShopInfo]])
async def list_shops(
    query: ShopListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Shop)
    count_stmt = select(func.count(Shop.id))

    if query.keyword:
        stmt = stmt.where(Shop.name.contains(query.keyword))
        count_stmt = count_stmt.where(Shop.name.contains(query.keyword))
    if query.status is not None:
        stmt = stmt.where(Shop.status == query.status)
        count_stmt = count_stmt.where(Shop.status == query.status)

    total = await db.execute(count_stmt)
    total = total.scalar()

    stmt = stmt.offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(stmt)
    shops = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[ShopInfo.model_validate(shop) for shop in shops],
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    )


@router.get("/{shop_id}", response_model=ResponseSchema[ShopDetail])
async def get_shop_detail(shop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")

    categories_result = await db.execute(
        select(Category).where(Category.shop_id == shop_id).order_by(Category.sort_order)
    )
    categories = categories_result.scalars().all()

    shop_data = ShopDetail(
        id=shop.id,
        user_id=shop.user_id,
        name=shop.name,
        logo=shop.logo,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        business_hours=shop.business_hours,
        notice=shop.notice,
        rating=shop.rating,
        status=shop.status,
        created_at=shop.created_at,
        updated_at=shop.updated_at,
        categories=[]
    )

    for cat in categories:
        products_result = await db.execute(
            select(Product).where(Product.category_id == cat.id, Product.status == ProductStatus.ON.value)
        )
        products = products_result.scalars().all()

        cat_data = CategoryInfo(
            id=cat.id,
            shop_id=cat.shop_id,
            name=cat.name,
            sort_order=cat.sort_order,
            created_at=cat.created_at,
            products=[]
        )
        for product in products:
            cat_data.products.append(ProductInfo.model_validate(product))
        shop_data.categories.append(cat_data)

    return ResponseSchema(code=0, data=shop_data)


@router.post("/category", response_model=ResponseSchema[CategoryInfo])
async def create_category(
    request: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Shop).where(Shop.id == request.shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该店铺")

    category = Category(**request.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    cat_data = CategoryInfo(
        id=category.id,
        shop_id=category.shop_id,
        name=category.name,
        sort_order=category.sort_order,
        created_at=category.created_at,
        products=[],
    )
    return ResponseSchema(code=0, message="创建成功", data=cat_data)


@router.get("/category/{shop_id}", response_model=ResponseSchema[List[CategoryInfo]])
async def list_categories(shop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category).where(Category.shop_id == shop_id).order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    return ResponseSchema(
        code=0,
        data=[CategoryInfo.model_validate(cat) for cat in categories]
    )


@router.put("/category/{category_id}", response_model=ResponseSchema[CategoryInfo])
async def update_category(
    category_id: int,
    request: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise BadRequestException("分类不存在")

    shop_result = await db.execute(select(Shop).where(Shop.id == category.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该分类")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    cat_data = CategoryInfo(
        id=category.id,
        shop_id=category.shop_id,
        name=category.name,
        sort_order=category.sort_order,
        created_at=category.created_at,
        products=[],
    )
    return ResponseSchema(code=0, message="更新成功", data=cat_data)


@router.delete("/category/{category_id}", response_model=ResponseSchema)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise BadRequestException("分类不存在")

    shop_result = await db.execute(select(Shop).where(Shop.id == category.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该分类")

    await db.delete(category)
    await db.commit()
    return ResponseSchema(code=0, message="删除成功")


@router.post("/product", response_model=ResponseSchema[ProductInfo])
async def create_product(
    request: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Shop).where(Shop.id == request.shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该店铺")

    product = Product(**request.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return ResponseSchema(code=0, message="创建成功", data=ProductInfo.model_validate(product))


@router.get("/product/{shop_id}", response_model=ResponseSchema[PageResponse[ProductInfo]])
async def list_products(
    shop_id: int,
    query: ProductListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Product).where(Product.shop_id == shop_id)
    count_stmt = select(func.count(Product.id)).where(Product.shop_id == shop_id)

    if query.keyword:
        stmt = stmt.where(Product.name.contains(query.keyword))
        count_stmt = count_stmt.where(Product.name.contains(query.keyword))
    if query.category_id:
        stmt = stmt.where(Product.category_id == query.category_id)
        count_stmt = count_stmt.where(Product.category_id == query.category_id)
    if query.status is not None:
        stmt = stmt.where(Product.status == query.status)
        count_stmt = count_stmt.where(Product.status == query.status)

    total = await db.execute(count_stmt)
    total = total.scalar()

    stmt = stmt.offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[ProductInfo.model_validate(p) for p in products],
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    )


@router.get("/product/detail/{product_id}", response_model=ResponseSchema[ProductInfo])
async def get_product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise BadRequestException("商品不存在")
    return ResponseSchema(code=0, data=ProductInfo.model_validate(product))


@router.put("/product/{product_id}", response_model=ResponseSchema[ProductInfo])
async def update_product(
    product_id: int,
    request: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise BadRequestException("商品不存在")

    shop_result = await db.execute(select(Shop).where(Shop.id == product.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该商品")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return ResponseSchema(code=0, message="更新成功", data=ProductInfo.model_validate(product))


@router.delete("/product/{product_id}", response_model=ResponseSchema)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise BadRequestException("商品不存在")

    shop_result = await db.execute(select(Shop).where(Shop.id == product.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop.user_id != current_user.id:
        raise ForbiddenException("无权操作该商品")

    await db.delete(product)
    await db.commit()
    return ResponseSchema(code=0, message="删除成功")


@router.get("/my/orders", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def get_shop_orders(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    stmt = select(Order).where(Order.shop_id == shop.id)
    count_stmt = select(func.count(Order.id)).where(Order.shop_id == shop.id)

    if query.status:
        stmt = stmt.where(Order.status == query.status)
        count_stmt = count_stmt.where(Order.status == query.status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    stmt = stmt.order_by(Order.created_at.desc()).offset((query.page - 1) * query.page_size).limit(query.page_size)

    result = await db.execute(stmt)
    orders = result.scalars().all()

    order_list = []
    for order in orders:
        order_data = OrderResponse.model_validate(order)
        order_data.shop_name = shop.name
        order_data.shop_image = shop.logo
        order_data.address_info = AddressInfo(
            contact_name="",
            contact_phone=order.phone,
            address=order.address
        )
        order_list.append(order_data)

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=order_list,
            total=total,
            page=query.page,
            page_size=query.page_size,
        ),
    )


@router.get("/my/orders/{order_id}", response_model=ResponseSchema[OrderResponse])
async def get_shop_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    result = await db.execute(select(Order).where(Order.id == order_id, Order.shop_id == shop.id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")

    order_data = OrderResponse.model_validate(order)
    order_data.shop_name = shop.name
    order_data.shop_image = shop.logo
    order_data.address_info = AddressInfo(
        contact_name="",
        contact_phone=order.phone,
        address=order.address
    )

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

    return ResponseSchema(code=0, data=order_data)


@router.put("/my/orders/{order_id}/accept", response_model=ResponseSchema[OrderResponse])
async def accept_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    result = await db.execute(select(Order).where(Order.id == order_id, Order.shop_id == shop.id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.PENDING_ACCEPT:
        raise BadRequestException("订单状态异常")

    order.status = OrderStatus.ACCEPTED
    await db.commit()
    await db.refresh(order)
    logger.info(f"Order accepted: {order_id}")

    return ResponseSchema(code=0, message="接单成功", data=OrderResponse.model_validate(order))


@router.put("/my/orders/{order_id}/reject", response_model=ResponseSchema[OrderResponse])
async def reject_order(
    order_id: int,
    reason: str = Body(..., embed=True, description="拒单原因"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    result = await db.execute(select(Order).where(Order.id == order_id, Order.shop_id == shop.id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.PENDING_ACCEPT:
        raise BadRequestException("订单状态异常")

    original_status = order.status
    order.status = OrderStatus.CANCELLED
    order.reject_reason = reason

    if original_status == OrderStatus.PENDING_ACCEPT:
        from app.services.finance import FinanceService
        user_result = await db.execute(select(User).where(User.id == order.user_id))
        order_user = user_result.scalar_one_or_none()
        if order_user:
            await FinanceService.process_refund(
                db=db,
                order=order,
                user=order_user,
                refund_amount=order.total_amount,
                refund_type="AUTO_REFUND",
                reason=f"商家拒单: {reason}"
            )
            logger.info(f"Refund processed for rejected order: {order_id}")

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    for item in items_result.scalars().all():
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            product.stock += item.quantity

    await db.commit()
    await db.refresh(order)
    logger.info(f"Order rejected: {order_id}, reason: {reason}")

    return ResponseSchema(code=0, message="拒单成功", data=OrderResponse.model_validate(order))


@router.put("/my/orders/{order_id}/ready", response_model=ResponseSchema[OrderResponse])
async def order_ready(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    result = await db.execute(select(Order).where(Order.id == order_id, Order.shop_id == shop.id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.ACCEPTED:
        raise BadRequestException("订单状态异常")

    order.status = OrderStatus.READY
    await db.commit()
    await db.refresh(order)
    logger.info(f"Order ready: {order_id}")

    return ResponseSchema(code=0, message="备餐完成", data=OrderResponse.model_validate(order))


@router.get("/my/stats", response_model=ResponseSchema[dict])
async def get_shop_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    today_count_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.shop_id == shop.id,
            Order.status != OrderStatus.CANCELLED,
        )
    )
    total_orders = today_count_result.scalar() or 0

    today_revenue_result = await db.execute(
        select(func.sum(Order.total_amount)).where(
            Order.shop_id == shop.id,
            Order.status == OrderStatus.COMPLETED,
        )
    )
    total_revenue = today_revenue_result.scalar() or 0.0

    pending_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.shop_id == shop.id,
            Order.status.in_([OrderStatus.PENDING_ACCEPT, OrderStatus.ACCEPTED, OrderStatus.READY]),
        )
    )
    pending_orders = pending_result.scalar() or 0

    return ResponseSchema(code=0, data={
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "rating": shop.rating,
    })


@router.get("/my/stats/trend", response_model=ResponseSchema[list])
async def get_shop_trend(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shop_result = await db.execute(select(Shop).where(Shop.user_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("您还没有店铺")

    result = []
    today = datetime.now().date()

    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())

        order_count_result = await db.execute(
            select(func.count(Order.id)).where(
                Order.shop_id == shop.id,
                Order.created_at >= date_start,
                Order.created_at <= date_end,
            )
        )
        order_count = order_count_result.scalar() or 0

        revenue_result = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.shop_id == shop.id,
                Order.created_at >= date_start,
                Order.created_at <= date_end,
                Order.status == OrderStatus.COMPLETED,
            )
        )
        revenue = float(revenue_result.scalar() or 0)

        result.append({
            "date": date.strftime("%m-%d"),
            "orders": order_count,
            "revenue": round(revenue, 2),
        })

    return ResponseSchema(code=0, data=result)
