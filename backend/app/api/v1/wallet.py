from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models.models import User, FundFlow
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, ForbiddenException, get_logger
from app.services.finance import FinanceService
from app.utils.log_mask import mask_amount

router = APIRouter(prefix="/wallet", tags=["钱包"])
logger = get_logger("wallet")


class AdminRechargeRequest(BaseModel):
    amount: Decimal


@router.get("", response_model=ResponseSchema[dict])
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await FinanceService.ensure_wallet_exists(db, current_user.id)

    total_income_result = await db.execute(
        select(func.sum(FundFlow.amount)).where(
            FundFlow.user_id == current_user.id,
            FundFlow.flow_type == "INCOME"
        )
    )
    total_income = total_income_result.scalar() or Decimal("0.00")

    total_expense_result = await db.execute(
        select(func.sum(FundFlow.amount)).where(
            FundFlow.user_id == current_user.id,
            FundFlow.flow_type == "EXPENSE"
        )
    )
    total_expense = total_expense_result.scalar() or Decimal("0.00")

    return ResponseSchema(code=0, data={
        "id": wallet.id,
        "balance": float(wallet.balance),
        "frozen_balance": float(wallet.frozen_balance),
        "total_income": float(total_income),
        "total_expense": float(total_expense),
    })


@router.post("/recharge/{user_id}", response_model=ResponseSchema[dict])
async def admin_recharge_user_wallet(
    user_id: int,
    request: AdminRechargeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可为用户充值")

    if user_id == current_user.id:
        raise BadRequestException("管理员不能给自己充值")

    try:
        result = await FinanceService.recharge_wallet(db, user_id, request.amount)
        await db.commit()
        logger.info(f"Admin {current_user.id} recharged user wallet: target_user_id={user_id}, amount={mask_amount(request.amount)}")
        from app.services.audit import log_audit, log_finance_audit
        await log_audit(db, action="ADMIN_RECHARGE", user_id=current_user.id, resource="wallet", resource_id=str(user_id), details={"target_user_id": user_id, "amount": float(request.amount)})
        await log_finance_audit(db, audit_type="ADMIN_RECHARGE", user_id=user_id, amount=float(request.amount), description=f"管理员{current_user.id}为用户{user_id}充值{request.amount}元")
        return ResponseSchema(code=0, message="用户充值成功", data={
            "user_id": user_id,
            "amount": float(result["amount"]),
            "balance": float(result["balance"]),
            "daily_total": float(result["daily_total"]),
        })
    except ValueError as e:
        raise BadRequestException(str(e))


@router.post("/recharge", response_model=ResponseSchema[dict])
async def request_recharge(
    amount: Decimal = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User self-service recharge request.

    In the current system, this processes the recharge immediately
    (admin approval flow can be added later).
    """
    try:
        result = await FinanceService.recharge_wallet(db, current_user.id, amount)
        await db.commit()
        logger.info(f"User {current_user.id} recharged wallet: amount={mask_amount(amount)}")
        from app.services.audit import log_finance_audit
        await log_finance_audit(db, audit_type="RECHARGE", user_id=current_user.id, amount=float(amount), description=f"用户充值{amount}元")
        return ResponseSchema(code=0, message="充值成功", data={
            "amount": float(result["amount"]),
            "balance": float(result["balance"]),
            "daily_total": float(result["daily_total"]),
        })
    except ValueError as e:
        raise BadRequestException(str(e))


@router.post("/withdraw", response_model=ResponseSchema[dict])
async def request_withdraw(
    amount: Decimal = Body(..., embed=True),
    method: str = Body(default="ALIPAY", embed=True),
    account: str = Body(default="", embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User withdrawal request for SHOP_OWNER and RIDER roles."""
    VALID_WITHDRAW_METHODS = ["ALIPAY", "WECHAT", "BANK_CARD"]
    if method not in VALID_WITHDRAW_METHODS:
        raise BadRequestException(f"不支持的提现方式，可选: {', '.join(VALID_WITHDRAW_METHODS)}")

    if current_user.role not in ("SHOP_OWNER", "RIDER"):
        raise ForbiddenException("仅商家和骑手可申请提现")

    if not account:
        raise BadRequestException("请输入收款账号")

    try:
        result = await FinanceService.process_withdrawal(
            db=db,
            user_id=current_user.id,
            amount=amount,
        )

        from app.models.models import WithdrawalRecord, WithdrawalStatus
        record = WithdrawalRecord(
            user_id=current_user.id,
            amount=amount,
            method=method,
            account=account,
            status=WithdrawalStatus.PENDING.value,
        )
        db.add(record)
        await db.commit()

        logger.info(f"User {current_user.id} withdrew {mask_amount(amount)}")
        from app.services.audit import log_audit, log_finance_audit
        await log_audit(db, action="WITHDRAW", user_id=current_user.id, resource="wallet", resource_id=str(current_user.id), details={"amount": float(amount), "method": method})
        await log_finance_audit(db, audit_type="WITHDRAWAL", user_id=current_user.id, amount=float(amount), description=f"用户提现{amount}元，方式:{method}")
        return ResponseSchema(code=0, message="提现申请已提交", data={
            "withdraw_id": record.id,
            "amount": float(amount),
            "status": record.status,
            "balance_after": float(result["balance_after"]),
        })
    except ValueError as e:
        raise BadRequestException(str(e))


@router.get("/transactions", response_model=ResponseSchema[PageResponse[dict]])
async def get_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    business_type: Optional[str] = None,
    flow_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FundFlow).where(FundFlow.user_id == current_user.id)
    count_stmt = select(func.count(FundFlow.id)).where(FundFlow.user_id == current_user.id)

    if business_type:
        stmt = stmt.where(FundFlow.business_type == business_type)
        count_stmt = count_stmt.where(FundFlow.business_type == business_type)

    if flow_type:
        stmt = stmt.where(FundFlow.flow_type == flow_type)
        count_stmt = count_stmt.where(FundFlow.flow_type == flow_type)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.order_by(FundFlow.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return ResponseSchema(
        code=0,
        data=PageResponse(
            items=[{
                "id": t.id,
                "flow_type": t.flow_type,
                "amount": float(t.amount),
                "balance_before": float(t.balance_before),
                "balance_after": float(t.balance_after),
                "business_type": t.business_type,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            } for t in transactions],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )
