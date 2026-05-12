
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import (
    User, Order, Review, Shop, OrderStatus,
)
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, get_logger

router = APIRouter(prefix="/reviews", tags=["评价"])
logger = get_logger("review")


@router.post("", response_model=ResponseSchema[ReviewResponse])
async def create_review(
    request: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order_result = await db.execute(
        select(Order).where(
            Order.id == request.order_id,
            Order.user_id == current_user.id,
        )
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.COMPLETED:
        raise BadRequestException("订单未完成，无法评价")

    existing_result = await db.execute(
        select(Review).where(Review.order_id == request.order_id)
    )
    if existing_result.scalar_one_or_none():
        raise BadRequestException("该订单已评价")

    review = Review(
        order_id=request.order_id,
        user_id=current_user.id,
        shop_id=order.shop_id,
        rider_id=order.rider_id,
        shop_rating=request.shop_rating,
        rider_rating=request.rider_rating,
        content=request.content,
    )
    db.add(review)

    shop_result = await db.execute(select(Shop).where(Shop.id == order.shop_id))
    shop = shop_result.scalar_one_or_none()

    if shop:
        ratings_result = await db.execute(
            select(func.avg(Review.shop_rating)).where(Review.shop_id == shop.id)
        )
        avg_rating = ratings_result.scalar() or request.shop_rating
        shop.rating = round(float(avg_rating), 1)

    await db.commit()
    await db.refresh(review)

    review_data = ReviewResponse.model_validate(review)
    review_data.user_nickname = current_user.nickname

    logger.info(f"Review created: order={request.order_id}, shop_rating={request.shop_rating}")
    return ResponseSchema(code=0, message="评价成功", data=review_data)


@router.get("/shop/{shop_id}", response_model=ResponseSchema[PageResponse[ReviewResponse]])
async def get_shop_reviews(
    shop_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Review).where(Review.shop_id == shop_id)
    count_stmt = select(func.count(Review.id)).where(Review.shop_id == shop_id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    review_list = []
    for review in reviews:
        review_data = ReviewResponse.model_validate(review)
        user_result = await db.execute(select(User).where(User.id == review.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            review_data.user_nickname = user.nickname
        review_list.append(review_data)

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=review_list,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get("/order/{order_id}", response_model=ResponseSchema[ReviewResponse])
async def get_order_review(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.order_id == order_id))
    review = result.scalar_one_or_none()
    if not review:
        raise BadRequestException("该订单暂无评价")

    review_data = ReviewResponse.model_validate(review)
    return ResponseSchema(code=0, data=review_data)
