from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (
        Index("idx_coupon_code", "code", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    remain_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserCoupon(Base):
    __tablename__ = "user_coupons"
    __table_args__ = (
        Index("idx_user_coupon_user_coupon", "user_id", "coupon_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    coupon_id: Mapped[int] = mapped_column(Integer, ForeignKey("coupons.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="UNUSED")
    claimed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", backref="user_coupons")
    coupon: Mapped["Coupon"] = relationship("Coupon", backref="user_coupons")