from enum import Enum as PyEnum


class UserRole(str, PyEnum):
    USER = "USER"
    SHOP_OWNER = "SHOP_OWNER"
    RIDER = "RIDER"
    ADMIN = "ADMIN"


class UserStatus(int, PyEnum):
    DISABLED = 0
    ACTIVE = 1


class ShopStatus(int, PyEnum):
    PENDING = 0
    APPROVED = 1
    REST = 2
    REJECTED = -1


class ProductStatus(int, PyEnum):
    OFF = 0
    ON = 1


class OrderStatus(str, PyEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PENDING_ACCEPT = "PENDING_ACCEPT"
    ACCEPTED = "ACCEPTED"
    READY = "READY"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EarningType(str, PyEnum):
    DELIVERY_FEE = "DELIVERY_FEE"
    BONUS = "BONUS"


class WithdrawalStatus(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CLOSED = "CLOSED"


class TradeType(str, PyEnum):
    PAY = "PAY"
    REFUND = "REFUND"
    RECHARGE = "RECHARGE"


class PayChannel(str, PyEnum):
    BALANCE = "BALANCE"
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"
    UNIONPAY = "UNIONPAY"


class AccountType(str, PyEnum):
    USER = "USER"
    SHOP = "SHOP"
    RIDER = "RIDER"
    PLATFORM = "PLATFORM"


class FlowType(str, PyEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    FREEZE = "FREEZE"
    UNFREEZE = "UNFREEZE"


class BusinessType(str, PyEnum):
    ORDER_PAY = "ORDER_PAY"
    ORDER_REFUND = "ORDER_REFUND"
    COMMISSION = "COMMISSION"
    WITHDRAW = "WITHDRAW"
    RECHARGE = "RECHARGE"
    BONUS = "BONUS"


class RefundStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RefundType(str, PyEnum):
    AUTO_REFUND = "AUTO_REFUND"
    MANUAL = "MANUAL"


class SettlementStatus(str, PyEnum):
    UNSETTLED = "UNSETTLED"
    SETTLED = "SETTLED"
    WITHDRAWN = "WITHDRAWN"


class ConfigKey(str, PyEnum):
    SHOP_COMMISSION_RATE = "SHOP_COMMISSION_RATE"
    RIDER_SERVICE_FEE_RATE = "RIDER_SERVICE_FEE_RATE"
    RIDER_COMMISSION_RATE = "RIDER_COMMISSION_RATE"
    MIN_WITHDRAWAL_AMOUNT = "MIN_WITHDRAWAL_AMOUNT"
    PLATFORM_NAME = "PLATFORM_NAME"
    PLATFORM_CONTACT = "PLATFORM_CONTACT"