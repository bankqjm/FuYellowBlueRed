from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import User, Shop, ShopEarning, PlatformCommission, Order, SettlementStatus
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import ForbiddenException, get_logger

router = APIRouter(prefix="/shop/earnings", tags=["商家收益"])


@router.get("/summary", response_model=ResponseSchema[dict])
async def get_shop_earnings_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "SHOP_OWNER":
        raise ForbiddenException("仅商家可访问")
    
    shop_result = await db.execute(select(Shop).where(Shop.owner_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise ForbiddenException("商家不存在")
    
    total_result = await db.execute(
        select(func.sum(ShopEarning.net_amount)).where(
            ShopEarning.shop_id == shop.id
        )
    )
    total_earnings = total_result.scalar() or 0.0
    
    settled_result = await db.execute(
        select(func.sum(ShopEarning.net_amount)).where(
            ShopEarning.shop_id == shop.id,
            ShopEarning.status == SettlementStatus.SETTLED.value
        )
    )
    settled_amount = settled_result.scalar() or 0.0
    
    unsettled_result = await db.execute(
        select(func.sum(ShopEarning.net_amount)).where(
            ShopEarning.shop_id == shop.id,
            ShopEarning.status == SettlementStatus.UNSETTLED.value
        )
    )
    unsettled_amount = unsettled_result.scalar() or 0.0
    
    count_result = await db.execute(
        select(func.count(ShopEarning.id)).where(ShopEarning.shop_id == shop.id)
    )
    order_count = count_result.scalar() or 0
    
    return ResponseSchema(code=0, data={
        "total_earnings": total_earnings,
        "settled_amount": settled_amount,
        "unsettled_amount": unsettled_amount,
        "order_count": order_count,
    })


@router.get("/list", response_model=ResponseSchema[PageResponse[dict]])
async def get_shop_earnings_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "SHOP_OWNER":
        raise ForbiddenException("仅商家可访问")
    
    shop_result = await db.execute(select(Shop).where(Shop.owner_id == current_user.id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise ForbiddenException("商家不存在")
    
    stmt = select(ShopEarning).where(ShopEarning.shop_id == shop.id)
    count_stmt = select(func.count(ShopEarning.id)).where(ShopEarning.shop_id == shop.id)
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(ShopEarning.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    earnings = result.scalars().all()
    
    earnings_list = []
    for e in earnings:
        order_result = await db.execute(select(Order).where(Order.id == e.order_id))
        order = order_result.scalar_one_or_none()
        
        earnings_list.append({
            "id": e.id,
            "order_id": e.order_id,
            "order_no": e.order_no,
            "goods_amount": e.goods_amount,
            "commission_rate": e.commission_rate,
            "commission_amount": e.commission_amount,
            "net_amount": e.net_amount,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "settled_at": e.settled_at.isoformat() if e.settled_at else None,
            "order_status": order.status.value if order else None,
        })
    
    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=earnings_list,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get("/commission/summary", response_model=ResponseSchema[dict])
async def get_platform_commission_summary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可访问")
    
    total_result = await db.execute(
        select(func.sum(PlatformCommission.total)).where(PlatformCommission.id > 0)
    )
    total_commission = total_result.scalar() or 0.0
    
    shop_commission_result = await db.execute(
        select(func.sum(PlatformCommission.shop_commission)).where(PlatformCommission.id > 0)
    )
    shop_commission = shop_commission_result.scalar() or 0.0
    
    rider_commission_result = await db.execute(
        select(func.sum(PlatformCommission.rider_service_fee)).where(PlatformCommission.id > 0)
    )
    rider_commission = rider_commission_result.scalar() or 0.0
    
    count_result = await db.execute(select(func.count(PlatformCommission.id)))
    order_count = count_result.scalar() or 0
    
    return ResponseSchema(code=0, data={
        "total_commission": total_commission,
        "shop_commission": shop_commission,
        "rider_commission": rider_commission,
        "order_count": order_count,
    })


@router.get("/commission/list", response_model=ResponseSchema[PageResponse[dict]])
async def get_platform_commission_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可访问")
    
    stmt = select(PlatformCommission).where(PlatformCommission.id > 0)
    count_stmt = select(func.count(PlatformCommission.id))
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(PlatformCommission.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[{
                "id": c.id,
                "order_id": c.order_id,
                "shop_commission": c.shop_commission,
                "rider_service_fee": c.rider_service_fee,
                "total": c.total,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            } for c in commissions],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )
