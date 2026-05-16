
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import (
    User, Order, Shop, OrderStatus, RiderEarning, WithdrawalRecord, WithdrawalStatus, Wallet,
)
from app.schemas.order import OrderResponse, OrderQuery
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, ForbiddenException, get_logger
from app.services.finance import FinanceService

router = APIRouter(prefix="/rider", tags=["骑手"])
logger = get_logger("rider")


@router.get("/orders/available", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def get_available_orders(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    stmt = select(Order).where(
        Order.status == OrderStatus.READY,
        Order.rider_id.is_(None),
    )
    count_stmt = select(func.count(Order.id)).where(
        Order.status == OrderStatus.READY,
        Order.rider_id.is_(None),
    )

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
            order_data.shop_image = shop.logo
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


@router.get("/orders/active", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def get_active_orders(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    stmt = select(Order).where(
        Order.rider_id == current_user.id,
        Order.status.in_([OrderStatus.DELIVERING]),
    )
    count_stmt = select(func.count(Order.id)).where(
        Order.rider_id == current_user.id,
        Order.status.in_([OrderStatus.DELIVERING]),
    )

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
            order_data.shop_image = shop.logo
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


@router.put("/orders/{order_id}/accept", response_model=ResponseSchema[OrderResponse])
async def accept_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.READY:
        raise BadRequestException("订单状态异常")
    if order.rider_id is not None:
        raise BadRequestException("订单已被接单")

    order.rider_id = current_user.id
    order.status = OrderStatus.DELIVERING
    await db.commit()
    await db.refresh(order)

    logger.info(f"Rider {current_user.id} accepted order {order_id}")
    return ResponseSchema(code=0, message="接单成功", data=OrderResponse.model_validate(order))


@router.put("/orders/{order_id}/deliver", response_model=ResponseSchema[OrderResponse])
async def deliver_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    result = await db.execute(select(Order).where(
        Order.id == order_id,
        Order.rider_id == current_user.id,
    ))
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在或无权操作")
    if order.status != OrderStatus.DELIVERING:
        raise BadRequestException("订单状态异常")

    commission_info = await FinanceService.calculate_order_commission(db, order)
    rider_income = commission_info["rider_income"]

    await FinanceService.add_rider_earning(
        db=db,
        rider_id=current_user.id,
        order_id=order.id,
        amount=rider_income
    )
    logger.info(f"Rider earning added: rider={current_user.id}, order={order_id}, amount={rider_income}")

    order.status = OrderStatus.COMPLETED
    await db.commit()
    await db.refresh(order)

    logger.info(f"Rider {current_user.id} delivered order {order_id}")
    return ResponseSchema(code=0, message="确认送达成功", data=OrderResponse.model_validate(order))


@router.get("/earnings", response_model=ResponseSchema[PageResponse[dict]])
async def get_earnings(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    stmt = select(RiderEarning).where(RiderEarning.rider_id == current_user.id)
    count_stmt = select(func.count(RiderEarning.id)).where(RiderEarning.rider_id == current_user.id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    stmt = (
        stmt.order_by(RiderEarning.created_at.desc())
        .offset((query.page - 1) * query.page_size)
        .limit(query.page_size)
    )

    result = await db.execute(stmt)
    earnings = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[{
                "id": e.id,
                "order_id": e.order_id,
                "amount": e.amount,
                "type": e.type,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            } for e in earnings],
            total=total,
            page=query.page,
            page_size=query.page_size,
        ),
    )


@router.get("/earnings/summary", response_model=ResponseSchema[dict])
async def get_earnings_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    total_result = await db.execute(
        select(func.sum(RiderEarning.amount)).where(RiderEarning.rider_id == current_user.id)
    )
    total_earnings = total_result.scalar() or 0.0

    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_result.scalar_one_or_none()
    balance = wallet.balance if wallet else 0.0

    return ResponseSchema(code=0, data={
        "total_earnings": total_earnings,
        "balance": balance,
    })


@router.post("/withdraw", response_model=ResponseSchema[dict])
async def withdraw(
    amount: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise BadRequestException("钱包不存在")

    if wallet.balance < amount:
        raise BadRequestException("余额不足")

    record = WithdrawalRecord(
        user_id=current_user.id,
        amount=amount,
        method="ALIPAY",
        account="模拟账户",
        status=WithdrawalStatus.COMPLETED.value,
    )
    db.add(record)

    wallet.balance -= amount
    await db.commit()

    logger.info(f"Rider {current_user.id} withdrew {amount}")
    return ResponseSchema(code=0, message="提现成功", data={
        "withdraw_id": record.id,
        "amount": amount,
    })


@router.get("/withdrawals", response_model=ResponseSchema[PageResponse[dict]])
async def get_withdrawal_records(
    query: OrderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "RIDER":
        raise ForbiddenException("仅骑手可访问")

    stmt = select(WithdrawalRecord).where(WithdrawalRecord.user_id == current_user.id)
    count_stmt = select(func.count(WithdrawalRecord.id)).where(WithdrawalRecord.user_id == current_user.id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    stmt = (
        stmt.order_by(WithdrawalRecord.created_at.desc())
        .offset((query.page - 1) * query.page_size)
        .limit(query.page_size)
    )

    result = await db.execute(stmt)
    records = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[{
                "id": r.id,
                "amount": r.amount,
                "method": r.method,
                "account": r.account,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            } for r in records],
            total=total,
            page=query.page,
            page_size=query.page_size,
        ),
    )
