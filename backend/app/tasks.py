from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Order, OrderStatus
from app.services.order_service import OrderService
from app.utils.delay_queue import delay_queue
from app.core import get_logger

logger = get_logger("tasks")


async def run_order_timeout_task(db: AsyncSession):
    """Process pending payment orders that have timed out"""
    
    async def handle_order_timeout(item_id: str):
        if not item_id.startswith("order:"):
            logger.debug(f"Skipping non-order item: {item_id}")
            return
        
        try:
            order_id = int(item_id.split(":")[1])
            
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            
            if not order:
                logger.debug(f"Order {order_id} not found, skipping")
                return
            
            if order.status != OrderStatus.PENDING_PAYMENT:
                logger.debug(f"Order {order_id} is no longer pending payment, status: {order.status}")
                return
            
            logger.info(f"Processing timeout for order: {order_id}, order_no: {order.order_no}")
            
            order_service = OrderService(db)
            await order_service.cancel_order(
                order_id=order_id,
                cancel_type="timeout",
                reason="订单超时未支付"
            )
            
            logger.info(f"Order {order_id} cancelled due to timeout")
            
        except ValueError:
            logger.error(f"Invalid order_id format: {item_id}")
        except Exception as e:
            logger.error(f"Failed to process order timeout {item_id}: {e}")
    
    processed = await delay_queue.process_ready_items(handle_order_timeout, batch_size=50)
    if processed > 0:
        logger.info(f"Processed {processed} timeout orders")
