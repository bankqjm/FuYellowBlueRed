from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.database import get_db
from app.models.models import User, Coupon, UserCoupon
from app.schemas.base import ResponseSchema, PageResponse, BaseSchema, DecimalField
from app.deps.auth import get_current_user, require_admin
from app.core import BadRequestException, NotFoundException, get_logger
from typing import Optional

router = APIRouter(prefix="/coupons", tags=["优惠券"])
logger = get_logger(__name__)


class CouponResponse(BaseSchema):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    discount_amount: DecimalField
    min_order_amount: DecimalField
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
    coupon_result = await db.execute(select(Coupon).where(Coupon.id == coupon_id).with_for_update())
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
    try:
        user_coupon = UserCoupon(user_id=current_user.id, coupon_id=coupon_id)
        db.add(user_coupon)
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BadRequestException("您已领取过该优惠券")
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
    order_amount: Decimal,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    coupon_result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = coupon_result.scalar_one_or_none()
    if not coupon:
        raise NotFoundException("优惠券不存在")

    user_coupon = (await db.execute(
        select(UserCoupon).where(
            UserCoupon.user_id == current_user.id,
            UserCoupon.coupon_id == coupon.id,
            UserCoupon.status == "UNUSED"
        )
    )).scalar_one_or_none()
    if not user_coupon:
        raise BadRequestException("您未拥有该优惠券或已使用")

    if order_amount < coupon.min_order_amount:
        raise BadRequestException(f"订单金额需满{coupon.min_order_amount}元才可使用该优惠券")

    discount = min(coupon.discount_amount, order_amount)
    return ResponseSchema(code=0, message="优惠券可用", data={
        "coupon_id": coupon_id,
        "discount_amount": float(discount),
        "final_amount": float(order_amount - discount),
    })


class CreateCouponRequest(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None
    discount_amount: DecimalField
    min_order_amount: DecimalField = Decimal("0.00")
    total_count: int
    valid_from: datetime
    valid_until: datetime


@router.post("/admin/create", response_model=ResponseSchema[CouponResponse])
async def create_coupon(
    body: CreateCouponRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(select(Coupon).where(Coupon.code == body.code))
    if existing.scalar_one_or_none():
        raise BadRequestException("优惠券代码已存在")

    coupon = Coupon(
        name=body.name,
        code=body.code,
        description=body.description,
        discount_amount=body.discount_amount,
        min_order_amount=body.min_order_amount,
        total_count=body.total_count,
        remain_count=body.total_count,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        status="ACTIVE",
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)

    logger.info(f"Admin {current_user.id} created coupon {coupon.id}")
    return ResponseSchema(code=0, message="创建成功", data=CouponResponse.model_validate(coupon))


@router.get("/admin/list", response_model=ResponseSchema[PageResponse[CouponResponse]])
async def admin_list_coupons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="ACTIVE, INACTIVE"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(Coupon)
    count_stmt = select(func.count(Coupon.id))

    if status:
        stmt = stmt.where(Coupon.status == status)
        count_stmt = count_stmt.where(Coupon.status == status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(Coupon.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    coupons = result.scalars().all()

    items = [CouponResponse.model_validate(c) for c in coupons]
    return ResponseSchema(code=0, data=PageResponse(items=items, total=total, page=page, page_size=page_size))


@router.put("/admin/{coupon_id}/status", response_model=ResponseSchema[CouponResponse])
async def update_coupon_status(
    coupon_id: int,
    status: str = Query(..., description="ACTIVE 或 INACTIVE"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if status not in ("ACTIVE", "INACTIVE"):
        raise BadRequestException("状态值必须为 ACTIVE 或 INACTIVE")

    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise NotFoundException("优惠券不存在")

    coupon.status = status
    await db.commit()
    await db.refresh(coupon)

    logger.info(f"Admin {current_user.id} updated coupon {coupon_id} status to {status}")
    return ResponseSchema(code=0, message="状态更新成功", data=CouponResponse.model_validate(coupon))
