import json
from datetime import datetime, timedelta
from app.utils.redis_client import redis_client
from app.core import get_logger

logger = get_logger("delay_queue")


class DelayQueue:
    def __init__(self, queue_name: str = "delay_queue"):
        self.queue_name = queue_name
        self.processing_set = f"{queue_name}:processing"
        self.processing_timeout = 60

    async def add(self, item_id: str, delay_seconds: int) -> bool:
        """Add an item to the delay queue with specified delay"""
        if not redis_client.is_connected:
            logger.warning("Redis not connected, cannot add to delay queue")
            return False
        
        try:
            score = int((datetime.now() + timedelta(seconds=delay_seconds)).timestamp())
            await redis_client.client.zadd(self.queue_name, {item_id: score})
            logger.debug(f"Added {item_id} to delay queue, expires at {score}")
            return True
        except Exception as e:
            logger.error(f"Failed to add {item_id} to delay queue: {e}")
            return False

    async def add_order_timeout(self, order_id: int, delay_minutes: int = 15) -> bool:
        """Add an order to the timeout queue"""
        return await self.add(f"order:{order_id}", delay_minutes * 60)

    async def remove(self, item_id: str) -> bool:
        """Remove an item from the delay queue"""
        if not redis_client.is_connected:
            return False
        
        try:
            result = await redis_client.client.zrem(self.queue_name, item_id)
            if result > 0:
                logger.debug(f"Removed {item_id} from delay queue")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to remove {item_id} from delay queue: {e}")
            return False

    async def remove_order(self, order_id: int) -> bool:
        """Remove an order from the timeout queue"""
        return await self.remove(f"order:{order_id}")

    async def get_ready_items(self, batch_size: int = 100) -> list:
        """Get items that are ready to be processed"""
        if not redis_client.is_connected:
            return []
        
        try:
            now = int(datetime.now().timestamp())
            items = await redis_client.client.zrangebyscore(
                self.queue_name, 0, now, start=0, num=batch_size
            )
            return [item.decode('utf-8') for item in items]
        except Exception as e:
            logger.error(f"Failed to get ready items from delay queue: {e}")
            return []

    async def lock_and_process(self, item_id: str) -> bool:
        """Lock an item for processing to prevent duplicate handling"""
        if not redis_client.is_connected:
            return True
        
        try:
            acquired = await redis_client.client.set(
                f"{self.processing_set}:{item_id}",
                "1",
                nx=True,
                ex=self.processing_timeout
            )
            return acquired is not None
        except Exception as e:
            logger.error(f"Failed to lock {item_id}: {e}")
            return False

    async def unlock(self, item_id: str):
        """Unlock an item after processing"""
        if not redis_client.is_connected:
            return
        
        try:
            await redis_client.client.delete(f"{self.processing_set}:{item_id}")
        except Exception as e:
            logger.error(f"Failed to unlock {item_id}: {e}")

    async def process_ready_items(self, handler, batch_size: int = 100) -> int:
        """Process all ready items using the provided handler function"""
        ready_items = await self.get_ready_items(batch_size)
        processed_count = 0
        
        for item_id in ready_items:
            if not await self.lock_and_process(item_id):
                logger.debug(f"Item {item_id} is being processed by another worker")
                continue
            
            try:
                await handler(item_id)
                await self.remove(item_id)
                processed_count += 1
                logger.debug(f"Processed {item_id}")
            except Exception as e:
                logger.error(f"Failed to process {item_id}: {e}")
            finally:
                await self.unlock(item_id)
        
        return processed_count

    async def get_pending_count(self) -> int:
        """Get the number of pending items in the queue"""
        if not redis_client.is_connected:
            return 0
        
        try:
            return await redis_client.client.zcard(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get pending count: {e}")
            return 0


delay_queue = DelayQueue()