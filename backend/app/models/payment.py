from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from .enums import PaymentStatus, TradeType, PayChannel, SettlementStatus, AccountType, FlowType, BusinessType, RefundStatus, RefundType


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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default=PayChannel.BALANCE.value)
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.SUCCESS.value)
    extra_data: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


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
    goods_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.10"))
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
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
    shop_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rider_service_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    business_type: Mapped[str] = mapped_column(String(20), nullable=False)
    related_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="fund_flows", foreign_keys=[user_id])


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
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    refund_type: Mapped[str] = mapped_column(String(20), default=RefundType.MANUAL.value)
    status: Mapped[str] = mapped_column(String(20), default=RefundStatus.SUCCESS.value)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())