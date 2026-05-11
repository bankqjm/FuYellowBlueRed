
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import Shop, ShopStatus, User
from app.schemas.shop import ShopInfo, ShopListQuery
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.utils.exceptions import ForbiddenException, BadRequestException

router = APIRouter(prefix="/admin", tags=["管理员"])


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

