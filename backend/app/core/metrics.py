from prometheus_client import Counter, Gauge, Histogram

ORDER_CREATED = Counter(
    "fyybr_order_created_total",
    "Total number of orders created",
)

ORDER_COMPLETED = Counter(
    "fyybr_order_completed_total",
    "Total number of orders completed",
)

ORDER_CANCELLED = Counter(
    "fyybr_order_cancelled_total",
    "Total number of orders cancelled",
)

ACTIVE_ORDERS = Gauge(
    "fyybr_active_orders",
    "Number of currently active orders",
)

ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
    "fyybr_active_websocket_connections",
    "Number of active WebSocket connections",
)

USER_REGISTRATIONS = Counter(
    "fyybr_user_registrations_total",
    "Total number of user registrations",
)

API_REQUEST_DURATION = Histogram(
    "fyybr_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REDIS_OPERATIONS = Counter(
    "fyybr_redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)

PAYMENT_TRANSACTIONS = Counter(
    "fyybr_payment_transactions_total",
    "Total payment transactions",
    ["type", "status"],
)
