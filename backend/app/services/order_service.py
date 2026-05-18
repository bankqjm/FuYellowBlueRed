import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.models.models import (
    CartItem,
    Order,
    OrderItem,
    UserAddress,
    Product,
    Shop,
    OrderStatus,
    ProductStatus,
)
from app.schemas.order import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderQuery,
)
from app.core import BadRequestException, NotFoundException
from app.services.base import BaseService


class OrderService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_cart(self, user_id: int) -> List[CartItemResponse]:
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()

        response_items = []
        for item in cart_items:
            product_result = await self.db.execute(select(Product).where(Product.id == item.product_id))
            product = product_result.scalar_one_or_none()

            shop_result = await self.db.execute(select(Shop).where(Shop.id == item.shop_id))
            shop = shop_result.scalar_one_or_none()

            item_data = CartItemResponse.model_validate(item)
            if product:
                item_data.product_name = product.name
                item_data.product_image = product.image
                item_data.product_price = product.price
            if shop:
                item_data.shop_name = shop.name
            response_items.append(item_data)

        return response_items

    async def add_to_cart(self, user_id: int, request: CartItemCreate) -> CartItemResponse:
        product_result = await self.db.execute(
            select(Product).where(
                Product.id == request.product_id,
                Product.shop_id == request.shop_id,
                Product.status == ProductStatus.ON,
            )
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise BadRequestException("商品不存在或已下架")

        result = await self.db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == request.product_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.quantity += request.quantity
            cart_item = existing
        else:
            cart_item = CartItem(
                user_id=user_id,
                **request.model_dump(),
            )
            self.db.add(cart_item)

        await self.commit()
        await self.refresh(cart_item)

        item_data = CartItemResponse.model_validate(cart_item)
        item_data.product_name = product.name
        item_data.product_image = product.image
        item_data.product_price = product.price

        shop_result = await self.db.execute(select(Shop).where(Shop.id == request.shop_id))
        shop = shop_result.scalar_one_or_none()
        if shop:
            item_data.shop_name = shop.name

        return item_data

    async def update_cart_item(self, user_id: int, item_id: int, request: CartItemUpdate) -> CartItemResponse:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.user_id == user_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise BadRequestException("购物车项不存在")

        if request.quantity is not None:
            cart_item.quantity = request.quantity

        await self.commit()
        await self.refresh(cart_item)

        return CartItemResponse.model_validate(cart_item)

    async def delete_cart_item(self, user_id: int, item_id: int):
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.user_id == user_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise BadRequestException("购物车项不存在")

        await self.db.delete(cart_item)
        await self.commit()

    async def clear_shop_cart(self, user_id: int, shop_id: int):
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.shop_id == shop_id,
            )
        )
        cart_items = result.scalars().all()

        for item in cart_items:
            await self.db.delete(item)

        await self.commit()

    async def create_order(self, user_id: int, request: OrderCreate) -> OrderResponse:
        addr_result = await self.db.execute(
            select(UserAddress).where(
                UserAddress.id == request.address_id,
                UserAddress.user_id == user_id,
            )
        )
        address = addr_result.scalar_one_or_none()
        if not address:
            raise NotFoundException("收货地址不存在")

        cart_result = await self.db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.shop_id == request.shop_id,
            )
        )
        cart_items = cart_result.scalars().all()
        if not cart_items:
            raise BadRequestException("购物车为空")

        shop_result = await self.db.execute(select(Shop).where(Shop.id == request.shop_id))
        shop = shop_result.scalar_one_or_none()
        if not shop:
            raise NotFoundException("店铺不存在")

        total_amount = 0.0
        order_items = []
        for cart_item in cart_items:
            product_result = await self.db.execute(
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
            user_id=user_id,
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
        self.db.add(order)
        await self.commit()
        await self.refresh(order)

        for product, quantity in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_image=product.image,
                price=product.price,
                quantity=quantity,
            )
            self.db.add(order_item)
            product.stock -= quantity

        for item in cart_items:
            await self.db.delete(item)

        await self.commit()

        order_data = OrderResponse.model_validate(order)
        order_data.shop_name = shop.name

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

        return order_data

    async def pay_order(self, user_id: int, order_id: int) -> OrderResponse:
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("订单不存在")
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise BadRequestException("订单状态异常")

        order.status = OrderStatus.PENDING_ACCEPT
        await self.commit()
        await self.refresh(order)

        return OrderResponse.model_validate(order)

    async def get_orders(self, user_id: int, query: OrderQuery) -> tuple[List[OrderResponse], int]:
        stmt = select(Order).where(Order.user_id == user_id)
        count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)

        if query.status:
            stmt = stmt.where(Order.status == query.status)
            count_stmt = count_stmt.where(Order.status == query.status)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        stmt = stmt.order_by(Order.created_at.desc()).offset((query.page - 1) * query.page_size).limit(query.page_size)

        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        order_list = []
        for order in orders:
            order_data = OrderResponse.model_validate(order)
            shop_result = await self.db.execute(select(Shop).where(Shop.id == order.shop_id))
            shop = shop_result.scalar_one_or_none()
            if shop:
                order_data.shop_name = shop.name
                order_data.shop_image = shop.logo
            items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
            order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]
            order_list.append(order_data)

        return order_list, total

    async def get_order_detail(self, user_id: int, order_id: int) -> OrderResponse:
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("订单不存在")

        order_data = OrderResponse.model_validate(order)

        shop_result = await self.db.execute(select(Shop).where(Shop.id == order.shop_id))
        shop = shop_result.scalar_one_or_none()
        if shop:
            order_data.shop_name = shop.name

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

        return order_data

    async def confirm_receipt(self, user_id: int, order_id: int) -> OrderResponse:
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("订单不存在")
        if order.status != OrderStatus.DELIVERING:
            raise BadRequestException("订单状态异常")

        order.status = OrderStatus.COMPLETED
        await self.commit()
        await self.refresh(order)

        return OrderResponse.model_validate(order)

    async def cancel_order(
        self,
        order_id: int,
        cancel_type: str = "user",
        reason: str = None,
    ) -> OrderResponse:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("订单不存在")
        if order.status not in (OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING_ACCEPT):
            raise BadRequestException("当前订单状态不可取消")

        if order.status == OrderStatus.PENDING_ACCEPT:
            from app.services.finance import FinanceService
            from app.models.models import User
            user_result = await self.db.execute(select(User).where(User.id == order.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                await FinanceService.process_refund(
                    db=self.db,
                    order=order,
                    user=user,
                    refund_amount=order.total_amount,
                    refund_type="AUTO_REFUND",
                    reason=reason or "系统取消订单"
                )

        order.status = OrderStatus.CANCELLED
        await self.commit()
        await self.refresh(order)

        logger.info(f"Order {order_id} cancelled by system, type: {cancel_type}")
        return OrderResponse.model_validate(order)
