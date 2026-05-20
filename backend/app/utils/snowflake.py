"""
Pure Python Snowflake ID generator for distributed unique ID generation.

Generates 64-bit IDs with the following structure:
- 1 bit sign (unused)
- 41 bits timestamp (millisecond precision, ~69 years from epoch)
- 10 bits machine id (worker_id 5 bits + datacenter_id 5 bits)
- 12 bits sequence number (4096 IDs per millisecond)

The epoch is set to 2024-01-01 00:00:00 UTC to maximize useful lifetime.
"""

import time
import threading
from datetime import datetime, timezone


class SnowflakeGenerator:
    """Thread-safe Snowflake ID generator with clock drift protection."""

    EPOCH = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1  # 31
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095

    WORKER_ID_SHIFT = SEQUENCE_BITS
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    def __init__(self, worker_id: int = 1, datacenter_id: int = 1):
        if worker_id < 0 or worker_id > self.MAX_WORKER_ID:
            raise ValueError(
                f"worker_id must be between 0 and {self.MAX_WORKER_ID}, got {worker_id}"
            )
        if datacenter_id < 0 or datacenter_id > self.MAX_DATACENTER_ID:
            raise ValueError(
                f"datacenter_id must be between 0 and {self.MAX_DATACENTER_ID}, got {datacenter_id}"
            )

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp

    def generate_id(self) -> int:
        """Generate a unique Snowflake ID. Thread-safe.

        Raises:
            RuntimeError: If system clock has moved backwards.
        """
        with self._lock:
            timestamp = self._current_millis()

            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    f"Clock moved backwards. Refusing to generate id for "
                    f"{self.last_timestamp - timestamp} milliseconds"
                )

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return (
                ((timestamp - self.EPOCH) << self.TIMESTAMP_SHIFT)
                | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
                | (self.worker_id << self.WORKER_ID_SHIFT)
                | self.sequence
            )

    def generate_str(self) -> str:
        """Generate a unique Snowflake ID as string."""
        return str(self.generate_id())


# Module-level singleton with defaults (worker_id=1, datacenter_id=1)
_default_generator = SnowflakeGenerator(worker_id=1, datacenter_id=1)


def generate_snowflake_id() -> int:
    """Generate a unique Snowflake ID using the default generator."""
    return _default_generator.generate_id()


def generate_snowflake_str() -> str:
    """Generate a unique Snowflake ID as string using the default generator."""
    return _default_generator.generate_str()


def generate_order_no() -> str:
    """Generate an order number using Snowflake algorithm.

    Returns a string representation of the Snowflake ID,
    guaranteed unique and within 32 characters.
    """
    return generate_snowflake_str()


def generate_trade_no() -> str:
    """Generate a trade number for payment transactions.

    Uses a 'T' prefix to distinguish from order numbers,
    followed by the Snowflake ID string.
    """
    return f"T{generate_snowflake_str()}"
