from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from .enums import ShopStatus, ProductStatus


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
    business_days: Mapped[str] = mapped_column(String(100), nullable=True)
    notice: Mapped[str] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(default=5.0)
    status: Mapped[int] = mapped_column(default=ShopStatus.PENDING.value)
    monthly_sales: Mapped[int] = mapped_column(default=0)
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("20.00"))
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("3.00"))
    delivery_time: Mapped[str] = mapped_column(String(20), default="30分钟")
    discounts: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="shops")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="shop", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="shop")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="shop")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="shop")


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
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    stock: Mapped[int] = mapped_column(default=0)
    sales: Mapped[int] = mapped_column(default=0)
    tags: Mapped[str] = mapped_column(String(500), nullable=True, comment="标签")
    rating: Mapped[float] = mapped_column(default=0.0, comment="评分")
    status: Mapped[int] = mapped_column(default=ProductStatus.ON.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    shop: Mapped["Shop"] = relationship("Shop", back_populates=None)
    category: Mapped["Category"] = relationship("Category", back_populates="products")