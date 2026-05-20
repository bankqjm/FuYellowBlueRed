from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
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
    Coupon,
    UserCoupon,
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
from app.core import BadRequestException, NotFoundException, get_logger
from app.services.base import BaseService
from app.utils.snowflake import generate_order_no
from app.utils.delay_queue import delay_queue
from app.utils.decimal_utils import to_decimal, ZERO

logger = get_logger("order_service")


class OrderService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_cart(self, user_id: int) -> List[CartItemResponse]:
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()

        if not cart_items:
            return []

        # PERF-REFORM-01: Batch IN queries instead of N+1 per-item queries
        product_ids = list({item.product_id for item in cart_items})
        shop_ids = list({item.shop_id for item in cart_items})

        products_result = await self.db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        product_map = {p.id: p for p in products_result.scalars().all()}

        shops_result = await self.db.execute(
            select(Shop).where(Shop.id.in_(shop_ids))
        )
        shop_map = {s.id: s for s in shops_result.scalars().all()}

        response_items = []
        for item in cart_items:
            item_data = CartItemResponse.model_validate(item)
            product = product_map.get(item.product_id)
            if product:
                item_data.product_name = product.name
                item_data.product_image = product.image
                item_data.product_price = product.price
            shop = shop_map.get(item.shop_id)
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
            raise BadRequestException("收货地址不存在")

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

        total_amount = ZERO
        order_items = []
        for cart_item in cart_items:
            # Lock the product row for stock safety (SEC-REFORM-04)
            product_result = await self.db.execute(
                select(Product).where(Product.id == cart_item.product_id).with_for_update()
            )
            product = product_result.scalar_one_or_none()
            if not product or product.status != ProductStatus.ON:
                raise BadRequestException(f"商品 {cart_item.product_id} 不存在或已下架")
            # Re-check stock after lock (SEC-REFORM-04: "lock then check" pattern)
            if product.stock < cart_item.quantity:
                raise BadRequestException(f"商品 {product.name} 库存不足")

            # Ensure price is Decimal for calculation (SQLite may return float for Numeric)
            price = to_decimal(product.price)
            total_amount += price * cart_item.quantity
            order_items.append((product, cart_item.quantity))

        delivery_fee = to_decimal(shop.delivery_fee) if shop.delivery_fee is not None else ZERO
        discount_amount = ZERO
        user_coupon = None

        if request.coupon_id:
            uc_result = await self.db.execute(
                select(UserCoupon, Coupon).join(Coupon, UserCoupon.coupon_id == Coupon.id).where(
                    UserCoupon.id == request.coupon_id,
                    UserCoupon.user_id == user_id,
                    UserCoupon.status == "UNUSED",
                )
            )
            uc_row = uc_result.one_or_none()
            if not uc_row:
                raise BadRequestException("优惠券不可用")
            user_coupon, coupon = uc_row
            now = datetime.now()
            if now < coupon.valid_from or now > coupon.valid_until:
                raise BadRequestException("优惠券已过期")
            subtotal = total_amount + delivery_fee
            min_order_amount = to_decimal(coupon.min_order_amount)
            if subtotal < min_order_amount:
                raise BadRequestException(f"订单金额需满{min_order_amount}元才可使用该优惠券")
            coupon_discount = to_decimal(coupon.discount_amount)
            discount_amount = min(coupon_discount, subtotal)

        final_amount = total_amount + delivery_fee - discount_amount

        # Use Snowflake for order_no (SEC-REFORM-02)
        order_no = generate_order_no()
        order = Order(
            order_no=order_no,
            user_id=user_id,
            shop_id=request.shop_id,
            address=address.address,
            latitude=address.latitude,
            longitude=address.longitude,
            phone=address.contact_phone,
            remark=request.remark,
            total_amount=final_amount,
            discount_amount=discount_amount,
            coupon_id=request.coupon_id,
            delivery_fee=delivery_fee,
            status=OrderStatus.PENDING_PAYMENT,
        )
        self.db.add(order)
        await self.db.flush()

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

        # Application-level stock validation for SQLite (SEC-REFORM-04)
        # SQLite silently ignores FOR UPDATE, so we verify stock >= 0 after deduction
        for product, quantity in order_items:
            if product.stock < 0:
                raise BadRequestException(f"商品 {product.name} 库存不足")

        for item in cart_items:
            await self.db.delete(item)

        await self.commit()
        await self.refresh(order)

        await delay_queue.add_order_timeout(order.id, delay_minutes=15)
        logger.debug(f"Added order {order.id} to delay queue for 15-minute timeout")

        order_data = OrderResponse.model_validate(order)
        order_data.shop_name = shop.name

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

        return order_data

    async def pay_order(self, user_id: int, order_id: int, channel: str = "BALANCE") -> OrderResponse:
        from app.models.models import User
        from app.services.finance import FinanceService

        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise BadRequestException("订单不存在")
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise BadRequestException("订单状态异常")

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise BadRequestException("用户不存在")

        await FinanceService.process_payment(
            db=self.db,
            order=order,
            user=user,
            channel=channel
        )
        logger.info(f"Payment processed for order: {order_id}")

        await delay_queue.remove_order(order_id)
        logger.debug(f"Removed order {order_id} from delay queue")

        order.status = OrderStatus.PENDING_ACCEPT
        await self.commit()
        await self.refresh(order)

        if order.coupon_id:
            uc_result = await self.db.execute(
                select(UserCoupon).where(UserCoupon.id == order.coupon_id)
            )
            user_coupon = uc_result.scalar_one_or_none()
            if user_coupon and user_coupon.status == "UNUSED":
                user_coupon.status = "USED"
                user_coupon.used_at = datetime.now()
                await self.commit()
                logger.info(f"Coupon {user_coupon.coupon_id} marked as used for order {order_id}")

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

        if not orders:
            return [], total

        # PERF-REFORM-01: Batch IN queries instead of N+1 per-order queries
        shop_ids = list({o.shop_id for o in orders})
        order_ids = list({o.id for o in orders})

        shops_result = await self.db.execute(
            select(Shop).where(Shop.id.in_(shop_ids))
        )
        shop_map = {s.id: s for s in shops_result.scalars().all()}

        items_result = await self.db.execute(
            select(OrderItem).where(OrderItem.order_id.in_(order_ids))
        )
        items_by_order: dict[int, list[OrderItem]] = {}
        for item in items_result.scalars().all():
            items_by_order.setdefault(item.order_id, []).append(item)

        order_list = []
        for order in orders:
            order_data = OrderResponse.model_validate(order)
            shop = shop_map.get(order.shop_id)
            if shop:
                order_data.shop_name = shop.name
                order_data.shop_image = shop.logo
            order_data.items = [
                OrderItemResponse.model_validate(item)
                for item in items_by_order.get(order.id, [])
            ]
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
            raise BadRequestException("订单不存在")

        order_data = OrderResponse.model_validate(order)

        # PERF-REFORM-01: Parallel batch queries instead of sequential
        shop_result = await self.db.execute(select(Shop).where(Shop.id == order.shop_id))
        shop = shop_result.scalar_one_or_none()
        if shop:
            order_data.shop_name = shop.name
            order_data.shop_image = shop.logo

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

        return order_data

    async def confirm_receipt(self, user_id: int, order_id: int) -> OrderResponse:
        from app.services.finance import FinanceService

        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise BadRequestException("订单不存在")
        if order.status != OrderStatus.DELIVERED:
            raise BadRequestException("订单状态异常，请等待骑手送达后确认")

        order.status = OrderStatus.COMPLETED
        await self.commit()
        await self.refresh(order)

        try:
            await FinanceService.process_order_settlement(self.db, order)
            logger.info(f"Order settlement processed for order: {order_id}")
        except Exception as e:
            logger.warning(f"Order settlement failed for order {order_id}: {e}")

        return OrderResponse.model_validate(order)

    async def cancel_order(
        self,
        order_id: int,
        cancel_type: str = "user",
        reason: str = None,
    ) -> OrderResponse:
        from app.services.finance import FinanceService
        from app.models.models import User

        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise BadRequestException("订单不存在")
        if order.status not in (OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING_ACCEPT):
            raise BadRequestException("当前订单状态不可取消")

        # If already paid, process refund
        if order.status == OrderStatus.PENDING_ACCEPT:
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

        # Return coupon if used
        if order.coupon_id:
            uc_result = await self.db.execute(
                select(UserCoupon).where(UserCoupon.id == order.coupon_id)
            )
            user_coupon = uc_result.scalar_one_or_none()
            if user_coupon and user_coupon.status == "USED":
                user_coupon.status = "UNUSED"
                user_coupon.used_at = None

        # Restore stock with row lock (SEC-REFORM-04)
        # PERF-REFORM-01: Batch IN query instead of N+1 per-item queries
        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_items = items_result.scalars().all()
        product_ids = [item.product_id for item in order_items]

        if product_ids:
            products_result = await self.db.execute(
                select(Product).where(Product.id.in_(product_ids)).with_for_update()
            )
            product_map = {p.id: p for p in products_result.scalars().all()}
            for item in order_items:
                product = product_map.get(item.product_id)
                if product:
                    product.stock += item.quantity

        order.status = OrderStatus.CANCELLED
        await self.commit()
        await self.refresh(order)

        order_data = OrderResponse.model_validate(order)

        shop_result = await self.db.execute(select(Shop).where(Shop.id == order.shop_id))
        shop = shop_result.scalar_one_or_none()
        if shop:
            order_data.shop_name = shop.name

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_data.items = [OrderItemResponse.model_validate(item) for item in items_result.scalars().all()]

        logger.info(f"Order {order_id} cancelled, type: {cancel_type}")
        return order_data
