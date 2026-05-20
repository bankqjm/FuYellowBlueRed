import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import AuditLog, FinanceAuditLog
from app.core import get_logger
from app.utils.log_mask import mask_amount

logger = get_logger("audit")

LARGE_AMOUNT_THRESHOLD = 5000.0
FREQUENT_WITHDRAWAL_THRESHOLD = 3
FREQUENT_WITHDRAWAL_WINDOW_HOURS = 1


async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: int = None,
    resource: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address,
        user_agent=user_agent[:255] if user_agent else None,
    )
    db.add(audit)
    await db.commit()
    logger.info(f"Audit: action={action}, user_id={user_id}, resource={resource}/{resource_id}")


async def log_finance_audit(
    db: AsyncSession,
    audit_type: str,
    user_id: int = None,
    amount: float = None,
    description: str = None,
    ip_address: str = None,
):
    is_alert = 0

    if amount and abs(amount) >= LARGE_AMOUNT_THRESHOLD:
        is_alert = 1
        logger.warning(f"Large amount alert: user_id={user_id}, type={audit_type}, amount={mask_amount(amount)}")

    if audit_type == "WITHDRAWAL" and user_id:
        cutoff = datetime.now() - __import__("datetime").timedelta(hours=FREQUENT_WITHDRAWAL_WINDOW_HOURS)
        result = await db.execute(
            select(func.count(FinanceAuditLog.id)).where(
                FinanceAuditLog.user_id == user_id,
                FinanceAuditLog.audit_type == "WITHDRAWAL",
                FinanceAuditLog.created_at >= cutoff,
            )
        )
        count = result.scalar() or 0
        if count >= FREQUENT_WITHDRAWAL_THRESHOLD:
            is_alert = 1
            logger.warning(f"Frequent withdrawal alert: user_id={user_id}, count={count}")

    audit = FinanceAuditLog(
        user_id=user_id,
        audit_type=audit_type,
        amount=amount,
        description=description,
        is_alert=is_alert,
        ip_address=ip_address,
    )
    db.add(audit)
    await db.commit()

    return is_alert == 1
