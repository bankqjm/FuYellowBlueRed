from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models.models import User, Wallet, FundFlow, PaymentTransaction
from app.schemas.base import ResponseSchema, PageResponse
from app.deps.auth import get_current_user
from app.core import BadRequestException, get_logger
from app.services.finance import FinanceService

router = APIRouter(prefix="/wallet", tags=["钱包"])
logger = get_logger("wallet")


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
    total_income = total_income_result.scalar() or 0.0
    
    total_expense_result = await db.execute(
        select(func.sum(FundFlow.amount)).where(
            FundFlow.user_id == current_user.id,
            FundFlow.flow_type == "EXPENSE"
        )
    )
    total_expense = total_expense_result.scalar() or 0.0
    
    return ResponseSchema(code=0, data={
        "id": wallet.id,
        "balance": wallet.balance,
        "frozen_balance": wallet.frozen_balance,
        "total_income": total_income,
        "total_expense": total_expense,
    })


@router.post("/recharge", response_model=ResponseSchema[dict])
async def recharge_wallet(
    amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if amount <= 0:
        raise BadRequestException("充值金额必须大于0")
    
    wallet = await FinanceService.ensure_wallet_exists(db, current_user.id)
    wallet.balance += amount
    
    await FinanceService.create_fund_flow(
        db=db,
        user_id=current_user.id,
        account_type="USER",
        flow_type="INCOME",
        amount=amount,
        business_type="RECHARGE",
        description=f"钱包充值: {amount:.2f}元"
    )
    
    await db.commit()
    await db.refresh(wallet)
    
    logger.info(f"Wallet recharged: user={current_user.id}, amount={amount}")
    
    return ResponseSchema(code=0, message="充值成功", data={
        "balance": wallet.balance,
        "recharged_amount": amount,
    })


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
                "amount": t.amount,
                "balance_before": t.balance_before,
                "balance_after": t.balance_after,
                "business_type": t.business_type,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            } for t in transactions],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )
