from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from app.database import get_db
from app.models.models import User, Shop, Favorite
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, NotFoundException, get_logger
from app.schemas.base import BaseSchema
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/favorites", tags=["收藏"])
logger = get_logger(__name__)


class FavoriteResponse(BaseSchema):
    id: int
    shop_id: int
    created_at: Optional[datetime] = None
    shop_name: Optional[str] = None
    shop_image: Optional[str] = None
    shop_rating: Optional[float] = None
    monthly_sales: Optional[int] = None
    delivery_time: Optional[str] = None
    min_order_amount: Optional[float] = None


@router.get("", response_model=ResponseSchema[PageResponse[FavoriteResponse]])
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Favorite, Shop).join(Shop, Favorite.shop_id == Shop.id).where(
        Favorite.user_id == current_user.id
    )
    count_stmt = select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(Favorite.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for favorite, shop in rows:
        item = FavoriteResponse(
            id=favorite.id,
            shop_id=favorite.shop_id,
            created_at=favorite.created_at,
            shop_name=shop.name,
            shop_image=shop.logo,
            shop_rating=shop.rating,
            monthly_sales=shop.monthly_sales,
            delivery_time=shop.delivery_time,
            min_order_amount=shop.min_order_amount,
        )
        items.append(item)

    return ResponseSchema(code=0, data=PageResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("/{shop_id}", response_model=ResponseSchema[FavoriteResponse])
async def add_favorite(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shop_result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise NotFoundException("店铺不存在")

    existing = await db.execute(
        select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.shop_id == shop_id)
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestException("已收藏过该店铺")

    favorite = Favorite(user_id=current_user.id, shop_id=shop_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    logger.info(f"User {current_user.id} favorited shop {shop_id}")
    return ResponseSchema(code=0, message="收藏成功", data=FavoriteResponse(
        id=favorite.id,
        shop_id=favorite.shop_id,
        created_at=favorite.created_at,
        shop_name=shop.name,
        shop_image=shop.logo,
    ))


@router.delete("/{shop_id}", response_model=ResponseSchema)
async def remove_favorite(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        delete(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.shop_id == shop_id)
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise NotFoundException("收藏记录不存在")

    logger.info(f"User {current_user.id} unfavorited shop {shop_id}")
    return ResponseSchema(code=0, message="取消收藏成功")


@router.get("/check/{shop_id}", response_model=ResponseSchema)
async def check_favorite(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(
        select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.shop_id == shop_id)
        )
    )
    is_favorited = existing.scalar_one_or_none() is not None
    return ResponseSchema(code=0, data={"is_favorited": is_favorited})
