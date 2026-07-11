
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
from app.utils.cache import (
    get_cached_dict, set_cached_dict, delete_cached, delete_cached_pattern,
    SHOP_DETAIL_TTL, PRODUCT_DETAIL_TTL, SHOP_LIST_TTL,
)

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
        business_days=request.business_days,
        notice=request.notice,
        status=ShopStatus.PENDING.value,
        rating=5.0
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    logger.info(f"Shop applied: {shop.id} by user {current_user.id}")

    # PERF-REFORM-02: Invalidate shop list cache on new shop
    await delete_cached_pattern("shops:page:*")

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
    result = await db.execute(select(Shop).where(Shop.user_id == current_user.id).limit(1))
    shop = result.scalars().first()
    if not shop:
        raise BadRequestException("您还未创建店铺")
    return ResponseSchema(code=0, data=ShopInfo.model_validate(shop))


@router.put("/my", response_model=ResponseSchema[ShopInfo])
async def update_my_shop(
    request: ShopUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Shop).where(Shop.user_id == current_user.id).limit(1))
    shop = result.scalars().first()
    if not shop:
        raise BadRequestException("您还未创建店铺")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shop, field, value)

    await db.commit()
    await db.refresh(shop)

    # PERF-REFORM-02: Invalidate shop cache on update
    await delete_cached(f"shop:{shop.id}")
    await delete_cached_pattern("shops:page:*")

    return ResponseSchema(code=0, message="更新成功", data=ShopInfo.model_validate(shop))


@router.get("/categories", response_model=ResponseSchema[list[CategoryInfo]])
async def list_all_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()

    if not categories:
        return ResponseSchema(code=0, data=[])

    # Batch query products for all categories
    cat_ids = [cat.id for cat in categories]
    products_result = await db.execute(
        select(Product).where(
            Product.category_id.in_(cat_ids),
            Product.status == ProductStatus.ON.value,
        )
    )
    products_by_cat: dict[int, list[Product]] = {}
    for p in products_result.scalars().all():
        products_by_cat.setdefault(p.category_id, []).append(p)

    category_list = []
    for cat in categories:
        cat_data = CategoryInfo(
            id=cat.id,
            shop_id=cat.shop_id,
            name=cat.name,
            sort_order=cat.sort_order,
            created_at=cat.created_at,
            products=[ProductInfo.model_validate(p) for p in products_by_cat.get(cat.id, [])]
        )
        category_list.append(cat_data)

    return ResponseSchema(code=0, data=category_list)


@router.get("/list", response_model=ResponseSchema[PageResponse[ShopInfo]])
async def list_shops(
    query: ShopListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # PERF-REFORM-02: Try cache first for shop list (no keyword search)
    cache_key = None
    if not query.keyword:
        cache_key = f"shops:page:{query.page}:{query.page_size}:{query.status}"
        cached = await get_cached_dict(cache_key)
        if cached:
            return ResponseSchema(code=0, data=PageResponse.model_validate(cached))

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

    page_data = PageResponse(
        items=[ShopInfo.model_validate(shop) for shop in shops],
        total=total,
        page=query.page,
        page_size=query.page_size
    )

    # Cache the result if no keyword search
    if cache_key:
        await set_cached_dict(cache_key, page_data.model_dump(), SHOP_LIST_TTL)

    return ResponseSchema(code=0, data=page_data)


@router.get("/search", response_model=ResponseSchema[PageResponse[ProductInfo]])
async def search_products(
    keyword: str = Query("", description="搜索关键词"),
    shop_id: int = Query(None, description="店铺ID筛选"),
    category_id: int = Query(None, description="分类ID筛选"),
    min_price: float = Query(None, description="最低价格"),
    max_price: float = Query(None, description="最高价格"),
    sort_by: str = Query(None, description="排序方式: price/sales/rating"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.status == ProductStatus.ON.value)
    count_stmt = select(func.count(Product.id)).where(Product.status == ProductStatus.ON.value)

    if keyword:
        stmt = stmt.where(
            Product.name.contains(keyword) | Product.description.contains(keyword)
        )
        count_stmt = count_stmt.where(
            Product.name.contains(keyword) | Product.description.contains(keyword)
        )
    
    if shop_id:
        stmt = stmt.where(Product.shop_id == shop_id)
        count_stmt = count_stmt.where(Product.shop_id == shop_id)
    
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
        count_stmt = count_stmt.where(Product.category_id == category_id)

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
        count_stmt = count_stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
        count_stmt = count_stmt.where(Product.price <= max_price)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    sort_mapping = {
        "price": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "sales": Product.sales.desc(),
        "rating": Product.rating.desc() if hasattr(Product, 'rating') else Product.sales.desc(),
    }
    order_clause = sort_mapping.get(sort_by, Product.sales.desc())
    stmt = stmt.order_by(order_clause).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[ProductInfo.model_validate(p) for p in products],
            total=total,
            page=page,
            page_size=page_size
        )
    )


@router.get("/{shop_id}", response_model=ResponseSchema[ShopDetail])
async def get_shop_detail(shop_id: int, db: AsyncSession = Depends(get_db)):
    # PERF-REFORM-02: Try cache first for shop detail
    cache_key = f"shop:{shop_id}"
    cached = await get_cached_dict(cache_key)
    if cached:
        return ResponseSchema(code=0, data=ShopDetail.model_validate(cached))

    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")

    categories_result = await db.execute(
        select(Category).where(Category.shop_id == shop_id).order_by(Category.sort_order)
    )
    categories = categories_result.scalars().all()

    # Batch query products for all categories
    cat_ids = [cat.id for cat in categories]
    products_by_cat: dict[int, list[Product]] = {}
    if cat_ids:
        products_result = await db.execute(
            select(Product).where(
                Product.category_id.in_(cat_ids),
                Product.status == ProductStatus.ON.value,
            )
        )
        for p in products_result.scalars().all():
            products_by_cat.setdefault(p.category_id, []).append(p)

    shop_data = ShopDetail(
        id=shop.id,
        user_id=shop.user_id,
        name=shop.name,
        logo=shop.logo,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        business_hours=shop.business_hours,
        business_days=shop.business_days,
        notice=shop.notice,
        rating=shop.rating,
        status=shop.status,
        monthly_sales=shop.monthly_sales,
        min_order_amount=shop.min_order_amount,
        delivery_fee=shop.delivery_fee,
        delivery_time=shop.delivery_time,
        discounts=shop.discounts,
        created_at=shop.created_at,
        updated_at=shop.updated_at,
        categories=[]
    )

    for cat in categories:
        cat_data = CategoryInfo(
            id=cat.id,
            shop_id=cat.shop_id,
            name=cat.name,
            sort_order=cat.sort_order,
            created_at=cat.created_at,
            products=[ProductInfo.model_validate(p) for p in products_by_cat.get(cat.id, [])]
        )
        shop_data.categories.append(cat_data)

    # PERF-REFORM-02: Cache the shop detail
    await set_cached_dict(cache_key, shop_data.model_dump(), SHOP_DETAIL_TTL)

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

    # PERF-REFORM-02: Invalidate shop detail cache on category change
    await delete_cached(f"shop:{request.shop_id}")

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
        data=[
            CategoryInfo(
                id=cat.id,
                shop_id=cat.shop_id,
                name=cat.name,
                sort_order=cat.sort_order,
                created_at=cat.created_at,
                products=[],
            )
            for cat in categories
        ]
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

    # PERF-REFORM-02: Invalidate shop detail cache on category update
    await delete_cached(f"shop:{category.shop_id}")

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

    # PERF-REFORM-02: Invalidate shop detail cache on category delete
    await delete_cached(f"shop:{category.shop_id}")

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

    # PERF-REFORM-02: Invalidate shop cache (product list changed)
    await delete_cached(f"shop:{request.shop_id}")

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
    if hasattr(query, 'min_price') and query.min_price is not None:
        stmt = stmt.where(Product.price >= query.min_price)
        count_stmt = count_stmt.where(Product.price >= query.min_price)
    if hasattr(query, 'max_price') and query.max_price is not None:
        stmt = stmt.where(Product.price <= query.max_price)
        count_stmt = count_stmt.where(Product.price <= query.max_price)

    total = await db.execute(count_stmt)
    total = total.scalar()

    sort_mapping = {
        "price": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "sales": Product.sales.desc(),
        "rating": Product.rating.desc() if hasattr(Product, 'rating') else Product.sales.desc(),
    }
    if hasattr(query, 'sort_by') and query.sort_by in sort_mapping:
        stmt = stmt.order_by(sort_mapping[query.sort_by])
    else:
        stmt = stmt.order_by(Product.created_at.desc())

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
    # PERF-REFORM-02: Try cache first for product detail
    cache_key = f"product:{product_id}"
    cached = await get_cached_dict(cache_key)
    if cached:
        return ResponseSchema(code=0, data=ProductInfo.model_validate(cached))

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise BadRequestException("商品不存在")

    product_data = ProductInfo.model_validate(product)
    await set_cached_dict(cache_key, product_data.model_dump(), PRODUCT_DETAIL_TTL)
    return ResponseSchema(code=0, data=product_data)


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

    # PERF-REFORM-02: Invalidate product and shop cache on update
    await delete_cached(f"product:{product_id}")
    await delete_cached(f"shop:{product.shop_id}")

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

    # PERF-REFORM-02: Invalidate product and shop cache on delete
    await delete_cached(f"product:{product_id}")
    await delete_cached(f"shop:{product.shop_id}")

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

    order.status = OrderStatus.CANCELLED
    order.reject_reason = reason

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
    order_items = items_result.scalars().all()
    product_ids = [item.product_id for item in order_items]

    if product_ids:
        products_result = await db.execute(
            select(Product).where(Product.id.in_(product_ids)).with_for_update()
        )
        product_map = {p.id: p for p in products_result.scalars().all()}
        for item in order_items:
            product = product_map.get(item.product_id)
            if product:
                product.stock += item.quantity

    await db.commit()
    await db.refresh(order)
    logger.info(f"Order rejected: {order_id}, reason: {reason}")

    # PERF-REFORM-02: Invalidate product caches for stock restore
    for pid in product_ids:
        await delete_cached(f"product:{pid}")

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
    total_revenue = float(today_revenue_result.scalar() or 0.0)

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
