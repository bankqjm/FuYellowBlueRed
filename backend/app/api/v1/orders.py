import uuid
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.models import (
    User,
    CartItem,
    Order,
    OrderItem,
    UserAddress,
    Product,
    Shop,
    OrderStatus,
    ProductStatus,
)
from app.services.finance import FinanceService
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
from app.core import BadRequestException, get_logger

router = APIRouter(prefix="/orders", tags=["订单"])
logger = get_logger("orders")


@router.get("/cart", response_model=ResponseSchema[list[CartItemResponse]])
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem).where(CartItem.user_id == current_user.id)
    )
    cart_items = result.scalars().all()

    response_items = []
    for item in cart_items:
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()

        shop_result = await db.execute(select(Shop).where(Shop.id == item.shop_id))
        shop = shop_result.scalar_one_or_none()

        item_data = CartItemResponse.model_validate(item)
        if product:
            item_data.product_name = product.name
            item_data.product_image = product.image
            item_data.product_price = product.price
        if shop:
            item_data.shop_name = shop.name
        response_items.append(item_data)

    return ResponseSchema(code=0, data=response_items)


@router.post("/cart", response_model=ResponseSchema[CartItemResponse])
async def add_to_cart(
    request: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(
        select(Product).where(
            Product.id == request.product_id,
            Product.shop_id == request.shop_id,
            Product.status == ProductStatus.ON,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise BadRequestException("商品不存在或已下架")

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.product_id == request.product_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.quantity += request.quantity
        cart_item = existing
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            **request.model_dump(),
        )
        db.add(cart_item)

    await db.commit()
    await db.refresh(cart_item)

    item_data = CartItemResponse.model_validate(cart_item)
    item_data.product_name = product.name
    item_data.product_image = product.image
    item_data.product_price = product.price

    shop_result = await db.execute(select(Shop).where(Shop.id == request.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop:
        item_data.shop_name = shop.name

    logger.info(f"Added to cart: user={current_user.id}, product={request.product_id}")
    return ResponseSchema(code=0, message="添加成功", data=item_data)


@router.put("/cart/{item_id}", response_model=ResponseSchema[CartItemResponse])
async def update_cart_item(
    item_id: int,
    request: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.user_id == current_user.id,
        )
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise BadRequestException("购物车项不存在")

    if request.quantity is not None:
        cart_item.quantity = request.quantity

    await db.commit()
    await db.refresh(cart_item)

    return ResponseSchema(code=0, message="更新成功", data=CartItemResponse.model_validate(cart_item))


@router.delete("/cart/{item_id}", response_model=ResponseSchema)
async def delete_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.user_id == current_user.id,
        )
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise BadRequestException("购物车项不存在")

    await db.delete(cart_item)
    await db.commit()

    return ResponseSchema(code=0, message="删除成功")


@router.delete("/cart/shop/{shop_id}", response_model=ResponseSchema)
async def clear_shop_cart(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.shop_id == shop_id,
        )
    )
    cart_items = result.scalars().all()

    for item in cart_items:
        await db.delete(item)

    await db.commit()
    return ResponseSchema(code=0, message="清空成功")


@router.post("/create", response_model=ResponseSchema[OrderResponse])
async def create_order(
    request: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    addr_result = await db.execute(
        select(UserAddress).where(
            UserAddress.id == request.address_id,
            UserAddress.user_id == current_user.id,
        )
    )
    address = addr_result.scalar_one_or_none()
    if not address:
        raise BadRequestException("收货地址不存在")

    cart_result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.shop_id == request.shop_id,
        )
    )
    cart_items = cart_result.scalars().all()
    if not cart_items:
        raise BadRequestException("购物车为空")

    shop_result = await db.execute(select(Shop).where(Shop.id == request.shop_id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise BadRequestException("店铺不存在")

    total_amount = 0.0
    order_items = []
    for cart_item in cart_items:
        product_result = await db.execute(
            select(Product).where(Product.id == cart_item.product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product or product.status != ProductStatus.ON:
            raise BadRequestException(f"商品 {cart_item.product_id} 不存在或已下架")
        if product.stock < cart_item.quantity:
            raise BadRequestException(f"商品 {product.name} 库存不足")

        total_amount += product.price * cart_item.quantity
        order_items.append((product, cart_item.quantity))

    delivery_fee = 5.0

    order_no = str(uuid.uuid4()).replace("-", "")[:32]
    order = Order(
        order_no=order_no,
        user_id=current_user.id,
        shop_id=request.shop_id,
        address=address.address,
        latitude=address.latitude,
        longitude=address.longitude,
        phone=address.contact_phone,
        remark=request.remark,
        total_amount=total_amount + delivery_fee,
        delivery_fee=delivery_fee,
        status=OrderStatus.PENDING_PAYMENT,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    for product, quantity in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_image=product.image,
            price=product.price,
            quantity=quantity,
        )
        db.add(order_item)
        product.stock -= quantity

    for item in cart_items:
        await db.delete(item)

    await db.commit()

    order_data = OrderResponse.model_validate(order)
    order_data.shop_name = shop.name
    logger.info(f"Order created: {order.id} by user {current_user.id}")
    return ResponseSchema(code=0, message="创建订单成功", data=order_data)


@router.post("/{order_id}/pay", response_model=ResponseSchema[OrderResponse])
async def pay_order(
    order_id: int,
    channel: str = Body(default="BALANCE"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise BadRequestException("订单状态异常")

    payment_result = await FinanceService.process_payment(
        db=db,
        order=order,
        user=current_user,
        channel=channel
    )
    logger.info(f"Payment processed: order={order_id}, {payment_result}")

    await FinanceService.process_order_settlement(db=db, order=order)

    order.status = OrderStatus.PENDING_ACCEPT
    await db.commit()
    await db.refresh(order)

    logger.info(f"Order paid and settled: {order_id}")
    return ResponseSchema(code=0, message="支付成功", data=OrderResponse.model_validate(order))


@router.get("/{order_id}", response_model=ResponseSchema[OrderResponse])
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")

    order_data = OrderResponse.model_validate(order)

    shop_result = await db.execute(select(Shop).where(Shop.id == order.shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop:
        order_data.shop_name = shop.name

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

    return ResponseSchema(code=0, data=order_data)


@router.get("", response_model=ResponseSchema[PageResponse[OrderResponse]])
async def list_orders(
    query: OrderQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Order).where(Order.user_id == current_user.id)
    count_stmt = select(func.count(Order.id)).where(Order.user_id == current_user.id)

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
            order_data.shop_image = shop.logo
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]
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


@router.put("/{order_id}/confirm", response_model=ResponseSchema[OrderResponse])
async def confirm_receipt(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status != OrderStatus.DELIVERING:
        raise BadRequestException("订单状态异常")

    order.status = OrderStatus.COMPLETED
    await db.commit()
    await db.refresh(order)

    logger.info(f"Order confirmed: {order_id}")
    return ResponseSchema(code=0, message="确认收货成功", data=OrderResponse.model_validate(order))


@router.put("/{order_id}/cancel", response_model=ResponseSchema[OrderResponse])
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise BadRequestException("订单不存在")
    if order.status not in (OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING_ACCEPT):
        raise BadRequestException("当前订单状态不可取消")

    if order.status == OrderStatus.PENDING_ACCEPT:
        await FinanceService.process_refund(
            db=db,
            order=order,
            user=current_user,
            refund_amount=order.total_amount,
            refund_type="AUTO_REFUND",
            reason="用户取消订单"
        )
        logger.info(f"Refund processed for cancelled order: {order_id}")

    order.status = OrderStatus.CANCELLED
    await db.commit()
    await db.refresh(order)

    logger.info(f"Order cancelled: {order_id} by user {current_user.id}")
    return ResponseSchema(code=0, message="取消订单成功", data=OrderResponse.model_validate(order))
