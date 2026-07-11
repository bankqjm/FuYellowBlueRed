from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.services.order_service import OrderService
from app.schemas.order import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderQuery,
)
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import get_logger

router = APIRouter(prefix="/orders", tags=["订单"])
logger = get_logger("orders")


@router.get("/cart", response_model=ResponseSchema[list[CartItemResponse]])
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    items = await service.get_cart(current_user.id)
    return ResponseSchema(code=0, data=items)


@router.post("/cart", response_model=ResponseSchema[CartItemResponse])
async def add_to_cart(
    request: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    item_data = await service.add_to_cart(current_user.id, request)
    logger.info(f"Added to cart: user={current_user.id}, product={request.product_id}")
    return ResponseSchema(code=0, message="添加成功", data=item_data)


@router.put("/cart/{item_id}", response_model=ResponseSchema[CartItemResponse])
async def update_cart_item(
    item_id: int,
    request: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    item_data = await service.update_cart_item(current_user.id, item_id, request)
    return ResponseSchema(code=0, message="更新成功", data=item_data)


@router.delete("/cart/{item_id}", response_model=ResponseSchema)
async def delete_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    await service.delete_cart_item(current_user.id, item_id)
    return ResponseSchema(code=0, message="删除成功")


@router.delete("/cart/shop/{shop_id}", response_model=ResponseSchema)
async def clear_shop_cart(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    await service.clear_shop_cart(current_user.id, shop_id)
    return ResponseSchema(code=0, message="清空成功")


@router.post("/create", response_model=ResponseSchema[OrderResponse])
async def create_order(
    request: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_data = await service.create_order(current_user.id, request)
    logger.info(f"Order created: {order_data.id} by user {current_user.id}")
    from app.services.audit import log_audit
    await log_audit(db, action="CREATE_ORDER", user_id=current_user.id, resource="order", resource_id=str(order_data.id), details={"shop_id": request.shop_id, "total_amount": float(order_data.total_amount) if hasattr(order_data, 'total_amount') else None})
    return ResponseSchema(code=0, message="创建订单成功", data=order_data)


@router.post("/{order_id}/pay", response_model=ResponseSchema[OrderResponse])
async def pay_order(
    order_id: int,
    channel: str = Body(default="BALANCE", embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_data = await service.pay_order(current_user.id, order_id, channel=channel)
    logger.info(f"Order paid: {order_id}")
    from app.services.audit import log_audit, log_finance_audit
    await log_audit(db, action="PAY_ORDER", user_id=current_user.id, resource="order", resource_id=str(order_id), details={"channel": channel})
    await log_finance_audit(db, audit_type="ORDER_PAY", user_id=current_user.id, amount=float(order_data.total_amount) if hasattr(order_data, 'total_amount') else 0, description=f"订单{order_id}支付，渠道:{channel}")
    return ResponseSchema(code=0, message="支付成功", data=order_data)


@router.get("/{order_id}", response_model=ResponseSchema[OrderResponse])
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_data = await service.get_order_detail(current_user.id, order_id)
    return ResponseSchema(code=0, data=order_data)


@router.get("", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def list_orders(
    query: OrderQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_list, total = await service.get_orders(current_user.id, query)
    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=order_list,
            total=total,
            page=query.page,
            page_size=query.page_size,
        ),
    )


@router.put("/{order_id}/confirm", response_model=ResponseSchema[OrderResponse])
async def confirm_receipt(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_data = await service.confirm_receipt(current_user.id, order_id)
    logger.info(f"Order confirmed: {order_id}")
    from app.services.audit import log_audit
    await log_audit(db, action="CONFIRM_RECEIPT", user_id=current_user.id, resource="order", resource_id=str(order_id))
    return ResponseSchema(code=0, message="确认收货成功", data=order_data)


@router.put("/{order_id}/cancel", response_model=ResponseSchema[OrderResponse])
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order_data = await service.cancel_order(order_id, cancel_type="user", reason="用户取消订单", user_id=current_user.id)
    logger.info(f"Order cancelled: {order_id} by user {current_user.id}")
    from app.services.audit import log_audit
    await log_audit(db, action="CANCEL_ORDER", user_id=current_user.id, resource="order", resource_id=str(order_id), details={"cancel_type": "user", "reason": "用户取消订单"})
    return ResponseSchema(code=0, message="取消订单成功", data=order_data)
