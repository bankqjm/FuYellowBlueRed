from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models.models import AuditLog, FinanceAuditLog, User, UserRole
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user, require_admin
from app.core import get_logger

router = APIRouter(prefix="/audit", tags=["审计日志"])
logger = get_logger("audit")


@router.get("/logs", response_model=ResponseSchema[PageResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog)
    count_stmt = select(func.count(AuditLog.id))

    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at) if log.created_at else None,
        })

    return ResponseSchema(data=PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.get("/finance", response_model=ResponseSchema[PageResponse])
async def list_finance_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    audit_type: str = Query(None),
    is_alert: int = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FinanceAuditLog)
    count_stmt = select(func.count(FinanceAuditLog.id))

    if audit_type:
        stmt = stmt.where(FinanceAuditLog.audit_type == audit_type)
        count_stmt = count_stmt.where(FinanceAuditLog.audit_type == audit_type)

    if is_alert is not None:
        stmt = stmt.where(FinanceAuditLog.is_alert == is_alert)
        count_stmt = count_stmt.where(FinanceAuditLog.is_alert == is_alert)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(desc(FinanceAuditLog.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "audit_type": log.audit_type,
            "amount": log.amount,
            "description": log.description,
            "is_alert": log.is_alert,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at) if log.created_at else None,
        })

    return ResponseSchema(data=PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))
