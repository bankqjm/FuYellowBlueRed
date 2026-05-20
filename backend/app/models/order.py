from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Index, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from .enums import OrderStatus, EarningType, WithdrawalStatus


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
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    coupon_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_coupons.id"), nullable=True)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING_PAYMENT.value)
    reject_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders", foreign_keys="Order.user_id")
    rider: Mapped["User"] = relationship("User", back_populates="rider_orders", foreign_keys="Order.rider_id")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", lazy="selectin")
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
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)

    order: Mapped["Order"] = relationship("Order", back_populates="items")


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

    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    shop: Mapped["Shop"] = relationship("Shop", foreign_keys=[shop_id])
    product: Mapped["Product"] = relationship("Product", foreign_keys=[product_id])


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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    account: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=WithdrawalStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())