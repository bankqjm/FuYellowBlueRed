
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models.models import Shop, ShopStatus, User, Order
from app.schemas.shop import ShopInfo, ShopListQuery
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import ForbiddenException, BadRequestException, get_logger

router = APIRouter(prefix="/admin", tags=["管理员"])
logger = get_logger("admin")


class UserInfo:
    def __init__(self, user: User):
        self.id = user.id
        self.phone = user.phone
        self.nickname = user.nickname
        self.avatar = user.avatar
        self.role = user.role
        self.status = user.status
        self.created_at = user.created_at


@router.put("/shop/{shop_id}/approve", response_model=ResponseSchema[ShopInfo])
async def approve_shop(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")

    shop.status = ShopStatus.APPROVED.value
    await db.commit()
    await db.refresh(shop)

    logger.info(f"Shop {shop_id} approved by admin {current_user.id}")
    return ResponseSchema(code=0, message="审核通过", data=ShopInfo.model_validate(shop))


@router.put("/shop/{shop_id}/reject", response_model=ResponseSchema[ShopInfo])
async def reject_shop(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")

    shop.status = ShopStatus.REJECTED.value
    await db.commit()
    await db.refresh(shop)

    logger.info(f"Shop {shop_id} rejected by admin {current_user.id}")
    return ResponseSchema(code=0, message="已拒绝", data=ShopInfo.model_validate(shop))


@router.get("/shop/pending", response_model=ResponseSchema[PageResponse[ShopInfo]])
async def list_pending_shops(
    query: ShopListQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    stmt = select(Shop).where(Shop.status == ShopStatus.PENDING.value)
    count_stmt = select(func.count(Shop.id)).where(Shop.status == ShopStatus.PENDING.value)

    if query.keyword:
        stmt = stmt.where(Shop.name.contains(query.keyword))
        count_stmt = count_stmt.where(Shop.name.contains(query.keyword))

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


@router.get("/users", response_model=ResponseSchema[PageResponse[dict]])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if keyword:
        stmt = stmt.where(User.phone.contains(keyword) | User.nickname.contains(keyword))
        count_stmt = count_stmt.where(User.phone.contains(keyword) | User.nickname.contains(keyword))
    if role:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)

    total = await db.execute(count_stmt)
    total = total.scalar()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[{
                "id": u.id,
                "phone": u.phone,
                "nickname": u.nickname,
                "avatar": u.avatar,
                "role": u.role,
                "status": u.status,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            } for u in users],
            total=total,
            page=page,
            page_size=page_size
        )
    )


@router.put("/users/{user_id}/status", response_model=ResponseSchema[dict])
async def update_user_status(
    user_id: int,
    status: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise BadRequestException("用户不存在")

    user.status = status
    await db.commit()

    logger.info(f"User {user_id} status updated to {status} by admin {current_user.id}")
    return ResponseSchema(code=0, message="更新成功", data={
        "id": user.id,
        "status": user.status,
    })


@router.get("/stats", response_model=ResponseSchema[dict])
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    user_count = await db.execute(select(func.count(User.id)))
    user_count = user_count.scalar()

    shop_count = await db.execute(select(func.count(Shop.id)))
    shop_count = shop_count.scalar()

    approved_shop_count = await db.execute(
        select(func.count(Shop.id)).where(Shop.status == ShopStatus.APPROVED.value)
    )
    approved_shop_count = approved_shop_count.scalar()

    order_count = await db.execute(select(func.count(Order.id)))
    order_count = order_count.scalar()

    pending_order_count = await db.execute(
        select(func.count(Order.id)).where(
            Order.status.in_(["PENDING_PAYMENT", "PENDING_ACCEPT", "ACCEPTED", "DELIVERING"])
        )
    )
    pending_order_count = pending_order_count.scalar()

    return ResponseSchema(code=0, data={
        "user_count": user_count,
        "shop_count": shop_count,
        "approved_shop_count": approved_shop_count,
        "order_count": order_count,
        "pending_order_count": pending_order_count,
    })


from app.schemas.order import OrderResponse, OrderQuery


@router.get("/orders", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def list_all_orders(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    stmt = select(Order)
    count_stmt = select(func.count(Order.id))

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
        shop_result = await db.execute(select(Shop).where(Shop.id == order.shop_id))
        shop = shop_result.scalar_one_or_none()
        if shop:
            order_data.shop_name = shop.name
        order_list.append(order_data)

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=order_list,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    )


@router.get("/orders/{order_id}", response_model=ResponseSchema[OrderResponse])
async def get_admin_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("无权限")

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")

    order_data = OrderResponse.model_validate(order)

    shop_result = await db.execute(select(Shop).where(Shop.id == order.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop:
        order_data.shop_name = shop.name

    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        order_data.user_phone = user.phone
        order_data.user_nickname = user.nickname

    return ResponseSchema(code=0, data=order_data)
