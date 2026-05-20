from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Order, OrderStatus
from app.services.order_service import OrderService
from app.utils.delay_queue import delay_queue
from app.utils.redis_client import redis_client
from app.core import get_logger as get_task_logger

logger = get_task_logger("order_timeout")


async def process_order_timeout(item_id: str, db: AsyncSession):
    """Process a single order timeout"""
    try:
        order_id = int(item_id.split(":")[1])
    except (IndexError, ValueError):
        logger.error(f"Invalid item_id format: {item_id}")
        return

    try:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            logger.warning(f"Order {order_id} not found, skipping")
            return

        if order.status != OrderStatus.PENDING_PAYMENT:
            logger.debug(f"Order {order_id} status is {order.status}, not pending payment")
            return

        service = OrderService(db)
        await service.cancel_order(
            order.id,
            cancel_type="timeout",
            reason="支付超时自动取消"
        )
        logger.info(f"Order {order_id} cancelled due to payment timeout")
    except Exception as e:
        logger.error(f"Failed to process order timeout {order_id}: {e}")


async def run_order_timeout_task(db: AsyncSession):
    """Process ready timeout orders from the delay queue"""
    if not redis_client.is_connected:
        logger.warning("Redis not connected, falling back to polling mode")
        return await _fallback_polling(db)

    async def handler(item_id: str):
        async with AsyncSessionLocal() as session:
            await process_order_timeout(item_id, session)
            await session.commit()

    processed = await delay_queue.process_ready_items(handler, batch_size=100)
    
    if processed > 0:
        logger.info(f"Order timeout task completed, processed {processed} orders")
    
    return processed


async def _fallback_polling(db: AsyncSession):
    """Fallback polling mode when Redis is not available"""
    
    # NOTE: Using naive datetime to match DB's naive DateTime columns.
    # In production with PostgreSQL, consider using timezone-aware datetimes
    # and ensure DB columns use DateTime(timezone=True).
    cutoff_time = datetime.now() - timedelta(minutes=15)
    result = await db.execute(
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
            service = OrderService(db)
            await service.cancel_order(
                order.id,
                cancel_type="timeout",
                reason="支付超时自动取消"
            )
            cancelled_count += 1
            logger.info(f"Order {order.id} cancelled due to payment timeout")
        except Exception as e:
            logger.error(f"Failed to cancel order {order.id}: {e}")

    return cancelled_count


from app.database import AsyncSessionLocal


class OrderTimeoutTask:
    """Backwards compatible class for order timeout processing"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def cancel_expired_orders(self) -> int:
        """Cancel expired pending payment orders"""
        if not redis_client.is_connected:
            return await _fallback_polling(self.db)
        
        async def handler(item_id: str):
            await process_order_timeout(item_id, self.db)
            await self.db.commit()
        
        processed = await delay_queue.process_ready_items(handler, batch_size=100)
        if processed > 0:
            logger.info(f"OrderTimeoutTask completed, processed {processed} orders")
        
        return processed
