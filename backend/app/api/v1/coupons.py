from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from app.database import get_db
from app.models.models import User, Coupon, UserCoupon
from app.schemas.base import ResponseSchema, PageResponse, BaseSchema
from app.deps.auth import get_current_user
from app.core import BadRequestException, NotFoundException, get_logger
from typing import Optional

router = APIRouter(prefix="/coupons", tags=["优惠券"])
logger = get_logger(__name__)


class CouponResponse(BaseSchema):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    discount_amount: float
    min_order_amount: float
    total_count: int
    remain_count: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str
    is_claimed: bool = False


class UserCouponResponse(BaseSchema):
    id: int
    coupon_id: int
    status: str
    claimed_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    coupon: Optional[CouponResponse] = None


@router.get("", response_model=ResponseSchema[PageResponse[CouponResponse]])
async def list_available_coupons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    stmt = select(Coupon).where(
        Coupon.status == "ACTIVE",
        Coupon.remain_count > 0,
        Coupon.valid_from <= now,
        Coupon.valid_until >= now,
    )
    count_stmt = select(func.count(Coupon.id)).where(
        Coupon.status == "ACTIVE",
        Coupon.remain_count > 0,
        Coupon.valid_from <= now,
        Coupon.valid_until >= now,
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(Coupon.discount_amount.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    coupons = result.scalars().all()

    items = [CouponResponse.model_validate(c) for c in coupons]
    return ResponseSchema(code=0, data=PageResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("/{coupon_id}/claim", response_model=ResponseSchema[UserCouponResponse])
async def claim_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    coupon_result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = coupon_result.scalar_one_or_none()
    if not coupon:
        raise NotFoundException("优惠券不存在")
    if coupon.status != "ACTIVE":
        raise BadRequestException("优惠券已下架")
    if coupon.remain_count <= 0:
        raise BadRequestException("优惠券已领完")
    now = datetime.now()
    if now < coupon.valid_from:
        raise BadRequestException("优惠券还未开始")
    if now > coupon.valid_until:
        raise BadRequestException("优惠券已过期")

    existing = await db.execute(
        select(UserCoupon).where(
            and_(UserCoupon.user_id == current_user.id, UserCoupon.coupon_id == coupon_id)
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestException("您已领取过该优惠券")

    coupon.remain_count -= 1
    user_coupon = UserCoupon(user_id=current_user.id, coupon_id=coupon_id)
    db.add(user_coupon)
    await db.commit()
    await db.refresh(user_coupon)
    await db.refresh(coupon)

    logger.info(f"User {current_user.id} claimed coupon {coupon_id}")
    return ResponseSchema(code=0, message="领取成功", data=UserCouponResponse(
        id=user_coupon.id,
        coupon_id=user_coupon.coupon_id,
        status=user_coupon.status,
        claimed_at=user_coupon.claimed_at,
        coupon=CouponResponse(**{**CouponResponse.model_validate(coupon).model_dump(), "is_claimed": True}),
    ))


@router.get("/my", response_model=ResponseSchema[PageResponse[UserCouponResponse]])
async def list_my_coupons(
    status: Optional[str] = Query(None, description="UNUSED, USED, EXPIRED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    stmt = select(UserCoupon, Coupon).join(Coupon, UserCoupon.coupon_id == Coupon.id).where(
        UserCoupon.user_id == current_user.id
    )
    count_stmt = select(func.count(UserCoupon.id)).where(UserCoupon.user_id == current_user.id)

    if status == "UNUSED":
        stmt = stmt.where(UserCoupon.status == "UNUSED")
        count_stmt = count_stmt.where(UserCoupon.status == "UNUSED")
    elif status == "USED":
        stmt = stmt.where(UserCoupon.status == "USED")
        count_stmt = count_stmt.where(UserCoupon.status == "USED")
    elif status == "EXPIRED":
        stmt = stmt.where(
            UserCoupon.status == "UNUSED",
            Coupon.valid_until < now
        )
        count_stmt = count_stmt.where(
            UserCoupon.status == "UNUSED",
            Coupon.valid_until < now
        )

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(UserCoupon.claimed_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for user_coupon, coupon in rows:
        item = UserCouponResponse(
            id=user_coupon.id,
            coupon_id=user_coupon.coupon_id,
            status=user_coupon.status,
            claimed_at=user_coupon.claimed_at,
            used_at=user_coupon.used_at,
            coupon=CouponResponse(**{**CouponResponse.model_validate(coupon).model_dump(), "is_claimed": True}),
        )
        items.append(item)

    return ResponseSchema(code=0, data=PageResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("/apply", response_model=ResponseSchema)
async def apply_coupon(
    coupon_id: int,
    order_amount: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    coupon_result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = coupon_result.scalar_one_or_none()
    if not coupon:
        raise NotFoundException("优惠券不存在")

    if order_amount < coupon.min_order_amount:
        raise BadRequestException(f"订单金额需满{coupon.min_order_amount}元才可使用该优惠券")

    discount = min(coupon.discount_amount, order_amount)
    return ResponseSchema(code=0, message="优惠券可用", data={
        "coupon_id": coupon_id,
        "discount_amount": discount,
        "final_amount": order_amount - discount,
    })
