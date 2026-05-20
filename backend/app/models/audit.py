from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Index, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(50), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FinanceAuditLog(Base):
    __tablename__ = "finance_audit_logs"
    __table_args__ = (
        Index("idx_finance_audit_user_id", "user_id"),
        Index("idx_finance_audit_type", "audit_type"),
        Index("idx_finance_audit_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    audit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_alert: Mapped[int] = mapped_column(default=0)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())