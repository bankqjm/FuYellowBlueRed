from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from .enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value, index=True)
    status: Mapped[int] = mapped_column(default=UserStatus.ACTIVE.value, index=True)
    failed_login_count: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False)
    addresses: Mapped[list["UserAddress"]] = relationship("UserAddress", back_populates="user")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    fund_flows: Mapped[list["FundFlow"]] = relationship("FundFlow", back_populates="user")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user", foreign_keys="Review.user_id")
    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="user")
    rider_orders: Mapped[list["Order"]] = relationship("Order", back_populates="rider", foreign_keys="Order.rider_id")
    rider_reviews: Mapped[list["Review"]] = relationship("Review", back_populates="rider", foreign_keys="Review.rider_id")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="user")
    shops: Mapped[list["Shop"]] = relationship("Shop", back_populates="owner")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    frozen_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
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


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (Index("idx_favorite_user_shop", "user_id", "shop_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="favorites")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="favorites")