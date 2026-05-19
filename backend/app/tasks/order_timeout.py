from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Order, OrderStatus
from app.services.order_service import OrderService
from app.core import get_logger as get_task_logger

logger = get_task_logger("order_timeout")


class OrderTimeoutTask:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeout_minutes = 15

    async def cancel_expired_orders(self) -> int:
        cutoff_time = datetime.now() - timedelta(minutes=self.timeout_minutes)
        result = await self.db.execute(
            select(Order).where(
                and_(
                    Order.status == OrderStatus.PENDING_PAYMENT,
                    Order.created_at < cutoff_time,
                )
            )
        )
        expired_orders = result.scalars().all()
        cancelled_count = 0

        for order in expired_orders:
            try:
                service = OrderService(self.db)
                await service.cancel_order(order.id, cancel_type="timeout", reason="支付超时自动取消")
                cancelled_count += 1
                logger.info(f"Order {order.id} cancelled due to payment timeout")
            except Exception as e:
                logger.error(f"Failed to cancel order {order.id}: {e}")

        return cancelled_count


async def run_order_timeout_task(db: AsyncSession):
    task = OrderTimeoutTask(db)
    cancelled = await task.cancel_expired_orders()
    if cancelled > 0:
        logger.info(f"Order timeout task completed, cancelled {cancelled} orders")
    return cancelled
