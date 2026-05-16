from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Enum, DateTime, ForeignKey, Float, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


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
    CLOSED = "CLOSED"


class TradeType(str, PyEnum):
    PAY = "PAY"
    REFUND = "REFUND"


class PayChannel(str, PyEnum):
    BALANCE = "BALANCE"
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"


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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value, index=True)
    status: Mapped[int] = mapped_column(default=UserStatus.ACTIVE.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False)
    shops: Mapped[list["Shop"]] = relationship("Shop", back_populates="owner")
    addresses: Mapped[list["UserAddress"]] = relationship("UserAddress", back_populates="user")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    rider_orders: Mapped[list["Order"]] = relationship("Order", back_populates="rider", foreign_keys="Order.rider_id")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance: Mapped[float] = mapped_column(default=0.0)
    frozen_balance: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="wallet")


class UserAddress(Base):
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    is_default: Mapped[int] = mapped_column(default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="addresses")


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        Index("idx_shops_status", "status"),
        Index("idx_shops_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    logo: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    business_hours: Mapped[str] = mapped_column(String(100), nullable=True)
    notice: Mapped[str] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(default=5.0)
    status: Mapped[int] = mapped_column(default=ShopStatus.PENDING.value)
    monthly_sales: Mapped[int] = mapped_column(default=0)
    min_order_amount: Mapped[float] = mapped_column(Float, default=20.0)
    delivery_fee: Mapped[float] = mapped_column(Float, default=3.0)
    delivery_time: Mapped[str] = mapped_column(String(20), default="30分钟")
    discounts: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="shops")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="shop", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="shop")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="shop")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("idx_categories_shop_id", "shop_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shop: Mapped["Shop"] = relationship("Shop", back_populates="categories")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_shop_id", "shop_id"),
        Index("idx_products_category_id", "category_id"),
        Index("idx_products_status", "status"),
        Index("idx_products_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    stock: Mapped[int] = mapped_column(default=0)
    sales: Mapped[int] = mapped_column(default=0)
    status: Mapped[int] = mapped_column(default=ProductStatus.ON.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    shop: Mapped["Shop"] = relationship("Shop", back_populates=None)
    category: Mapped["Category"] = relationship("Category", back_populates="products")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_shop_id", "shop_id"),
        Index("idx_orders_rider_id", "rider_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    rider_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    remark: Mapped[str] = mapped_column(String(500), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING_PAYMENT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders", foreign_keys=[user_id])
    rider: Mapped["User"] = relationship("User", back_populates="rider_orders", foreign_keys=[rider_id])
    shop: Mapped["Shop"] = relationship("Shop", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    review: Mapped["Review"] = relationship("Review", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    product_image: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)

    order: Mapped["Order"] = relationship("Order", back_populates="items")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_reviews_shop_id", "shop_id"),
        Index("idx_reviews_user_id", "user_id"),
        Index("idx_reviews_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    rider_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    shop_rating: Mapped[int] = mapped_column(nullable=False)
    rider_rating: Mapped[int] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(String(500), nullable=True)
    images: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="review")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="reviews")


class RiderEarning(Base):
    __tablename__ = "rider_earnings"
    __table_args__ = (
        Index("idx_rider_earnings_rider_id", "rider_id"),
        Index("idx_rider_earnings_order_id", "order_id"),
        Index("idx_rider_earnings_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rider_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default=EarningType.DELIVERY_FEE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WithdrawalRecord(Base):
    __tablename__ = "withdrawal_records"
    __table_args__ = (
        Index("idx_withdrawal_records_user_id", "user_id"),
        Index("idx_withdrawal_records_status", "status"),
        Index("idx_withdrawal_records_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    account: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=WithdrawalStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        Index("idx_cart_items_user_id", "user_id"),
        Index("idx_cart_items_shop_id", "shop_id"),
        Index("idx_cart_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        Index("idx_payment_order_id", "order_id"),
        Index("idx_payment_user_id", "user_id"),
        Index("idx_payment_trade_no", "trade_no"),
        Index("idx_payment_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    trade_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    trade_type: Mapped[str] = mapped_column(String(20), default=TradeType.PAY.value)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default=PayChannel.BALANCE.value)
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.SUCCESS.value)
    extra_data: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class ShopEarning(Base):
    __tablename__ = "shop_earnings"
    __table_args__ = (
        Index("idx_shop_earning_shop_id", "shop_id"),
        Index("idx_shop_earning_order_id", "order_id"),
        Index("idx_shop_earning_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    goods_amount: Mapped[float] = mapped_column(Float, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.10)
    commission_amount: Mapped[float] = mapped_column(Float, nullable=False)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SettlementStatus.UNSETTLED.value)
    settled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shop: Mapped["Shop"] = relationship("Shop", backref="earnings")


class PlatformCommission(Base):
    __tablename__ = "platform_commissions"
    __table_args__ = (
        Index("idx_platform_commission_order_id", "order_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    shop_commission: Mapped[float] = mapped_column(Float, nullable=False)
    rider_service_fee: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FundFlow(Base):
    __tablename__ = "fund_flows"
    __table_args__ = (
        Index("idx_fund_flow_user_id", "user_id"),
        Index("idx_fund_flow_account_type", "account_type"),
        Index("idx_fund_flow_business_type", "business_type"),
        Index("idx_fund_flow_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    flow_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_before: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    business_type: Mapped[str] = mapped_column(String(20), nullable=False)
    related_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", backref="fund_flows")


class RefundRecord(Base):
    __tablename__ = "refund_records"
    __table_args__ = (
        Index("idx_refund_order_id", "order_id"),
        Index("idx_refund_user_id", "user_id"),
        Index("idx_refund_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_transactions.id"), nullable=True)
    refund_amount: Mapped[float] = mapped_column(Float, nullable=False)
    refund_type: Mapped[str] = mapped_column(String(20), default=RefundType.MANUAL.value)
    status: Mapped[str] = mapped_column(String(20), default=RefundStatus.SUCCESS.value)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
