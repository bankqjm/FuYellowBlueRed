from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


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
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="reviews")
    rider: Mapped["User"] = relationship("User", foreign_keys=[rider_id], back_populates="rider_reviews")