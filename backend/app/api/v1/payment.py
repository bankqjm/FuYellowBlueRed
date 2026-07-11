"""充值API接口

提供用户充值功能，支持微信支付和银联云闪付。
在挡板模式下模拟支付流程。
"""

import json
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User, Wallet
from app.models.enums import PayChannel, PaymentStatus, TradeType, AccountType, FlowType, BusinessType
from app.models.payment import PaymentTransaction, FundFlow
from app.deps.auth import get_current_user
from app.core import BadRequestException
from app.schemas.base import ResponseSchema
from app.services.payment import (
    PaymentAdapterFactory,
    PaymentRequest,
    PaymentResultStatus,
    init_payment_adapters,
    get_payment_stub,
)
from app.utils.snowflake import generate_trade_no

router = APIRouter(prefix="/payment", tags=["支付充值"])

# 初始化支付适配器
init_payment_adapters()


class CreateRechargeRequest(BaseModel):
    """创建充值请求"""
    model_config = ConfigDict(json_schema_extra={"example": {"amount": 100.0, "channel": "WECHAT"}})
    amount: float = Field(..., gt=0, le=10000, description="充值金额(元)，最大1万")
    channel: str = Field(..., description="支付渠道: WECHAT / UNIONPAY")


class RechargeResponse(BaseModel):
    """充值响应"""
    trade_no: str
    amount: float
    channel: str
    status: str
    pay_url: str = ""
    qr_code: str = ""
    message: str = ""


class PaymentCallbackRequest(BaseModel):
    """支付回调请求"""
    trade_no: str
    channel: str
    channel_trade_no: str = ""
    status: str = "SUCCESS"


class RechargeRecordResponse(BaseModel):
    """充值记录"""
    id: int
    trade_no: str
    amount: float
    channel: str
    status: str
    created_at: str
    completed_at: Optional[str] = None


@router.post("/recharge", response_model=ResponseSchema[RechargeResponse])
async def create_recharge(
    request: CreateRechargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建充值订单"""
    if request.channel not in ("WECHAT", "UNIONPAY"):
        raise BadRequestException("不支持的支付渠道，请选择 WECHAT 或 UNIONPAY")

    # 检查钱包是否存在
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.user_id == current_user.id)
    )
    wallet = wallet_result.scalars().first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=Decimal("0"), frozen_balance=Decimal("0"))
        db.add(wallet)
        await db.flush()

    # 创建交易号
    trade_no = generate_trade_no()

    # 创建支付交易记录
    transaction = PaymentTransaction(
        order_id=0,  # 充值无关联订单
        user_id=current_user.id,
        trade_no=trade_no,
        trade_type=TradeType.RECHARGE.value,
        amount=Decimal(str(request.amount)),
        channel=request.channel,
        status=PaymentStatus.PENDING.value,
        extra_data=json.dumps({"channel": request.channel, "amount": float(request.amount)}),
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # 调用支付适配器创建支付
    try:
        adapter = PaymentAdapterFactory.get_adapter(request.channel)
        payment_request = PaymentRequest(
            trade_no=trade_no,
            amount=Decimal(str(request.amount)),
            subject=f"账户充值 {request.amount}元",
            body=f"用户{current_user.nickname or current_user.phone}充值{request.amount}元",
            user_id=current_user.id,
        )
        payment_response = await adapter.create_payment(payment_request)

        # 根据适配器返回状态同步更新交易记录
        if payment_response.status == PaymentResultStatus.SUCCESS:
            transaction.status = PaymentStatus.SUCCESS.value
            from datetime import datetime, timezone
            transaction.completed_at = datetime.now(timezone.utc)
            await db.commit()
        elif payment_response.status == PaymentResultStatus.TIMEOUT:
            transaction.status = PaymentStatus.TIMEOUT.value
            await db.commit()
        elif payment_response.status == PaymentResultStatus.FAILED:
            transaction.status = PaymentStatus.FAILED.value
            await db.commit()

        return ResponseSchema(code=0, data=RechargeResponse(
            trade_no=trade_no,
            amount=request.amount,
            channel=request.channel,
            status=payment_response.status.value,
            pay_url=payment_response.pay_url,
            qr_code=payment_response.qr_code,
            message=payment_response.message,
        ))
    except Exception as e:
        # 支付创建失败，更新交易状态
        transaction.status = PaymentStatus.FAILED.value
        await db.commit()
        raise BadRequestException(f"创建支付订单失败: {str(e)}")


@router.post("/recharge/confirm", response_model=ResponseSchema[dict])
async def confirm_recharge(
    request: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认充值（模拟回调）

    在挡板模式下，前端调用此接口模拟支付成功回调。
    真实环境下由支付平台回调。
    """
    if not PaymentAdapterFactory.is_stub_mode():
        raise BadRequestException("非挡板模式下请使用支付平台回调确认")

    # 查找交易记录
    result = await db.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.trade_no == request.trade_no,
            PaymentTransaction.user_id == current_user.id,
        )
    )
    transaction = result.scalars().first()
    if not transaction:
        raise BadRequestException("交易记录不存在")

    if transaction.status == PaymentStatus.SUCCESS.value:
        raise BadRequestException("该交易已处理")

    if transaction.status == PaymentStatus.FAILED.value:
        raise BadRequestException("该交易已失败，请重新发起充值")

    if transaction.status == PaymentStatus.TIMEOUT.value:
        raise BadRequestException("该交易已超时，请重新发起充值")

    if transaction.status == PaymentStatus.CLOSED.value:
        raise BadRequestException("该交易已关闭，请重新发起充值")

    # 更新交易状态
    transaction.status = (
        PaymentStatus.SUCCESS.value
        if request.status == "SUCCESS"
        else PaymentStatus.FAILED.value
    )
    transaction.extra_data = json.dumps({"channel_trade_no": request.channel_trade_no, "channel": request.channel})

    if transaction.status == PaymentStatus.SUCCESS.value:
        from datetime import datetime, timezone
        transaction.completed_at = datetime.now(timezone.utc)

        # 更新钱包余额
        wallet_result = await db.execute(
            select(Wallet).where(Wallet.user_id == current_user.id).with_for_update()
        )
        wallet = wallet_result.scalars().first()
        if not wallet:
            wallet = Wallet(user_id=current_user.id, balance=Decimal("0"), frozen_balance=Decimal("0"))
            db.add(wallet)
            await db.flush()

        balance_before = wallet.balance
        wallet.balance = wallet.balance + transaction.amount

        # 记录资金流水
        fund_flow = FundFlow(
            user_id=current_user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=transaction.amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            business_type=BusinessType.RECHARGE.value,
            related_id=transaction.id,
            description=f"充值{transaction.amount}元",
        )
        db.add(fund_flow)

    await db.commit()

    if transaction.status == PaymentStatus.SUCCESS.value:
        from app.services.audit import log_audit, log_finance_audit
        await log_audit(db, action="CONFIRM_RECHARGE", user_id=current_user.id, resource="payment", resource_id=request.trade_no, details={"amount": float(transaction.amount), "status": transaction.status})
        await log_finance_audit(db, audit_type="RECHARGE", user_id=current_user.id, amount=float(transaction.amount), description=f"充值确认{request.trade_no}，金额{transaction.amount}元")

    return ResponseSchema(
        code=0,
        data={"trade_no": request.trade_no, "status": transaction.status},
        message="充值成功" if transaction.status == PaymentStatus.SUCCESS.value else "充值失败",
    )


@router.get("/recharge/records", response_model=ResponseSchema[dict])
async def get_recharge_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取充值记录"""
    # 数据库端计数
    count_stmt = select(func.count(PaymentTransaction.id)).where(
        PaymentTransaction.user_id == current_user.id,
        PaymentTransaction.trade_type == TradeType.RECHARGE.value,
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页查询
    records_stmt = (
        select(PaymentTransaction)
        .where(
            PaymentTransaction.user_id == current_user.id,
            PaymentTransaction.trade_type == TradeType.RECHARGE.value,
        )
        .order_by(PaymentTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = (await db.execute(records_stmt)).scalars().all()

    items = [
        RechargeRecordResponse(
            id=r.id,
            trade_no=r.trade_no,
            amount=float(r.amount),
            channel=r.channel,
            status=r.status,
            created_at=str(r.created_at),
            completed_at=str(r.completed_at) if r.completed_at else None,
        )
        for r in records
    ]

    return ResponseSchema(code=0, data={
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/mock/scenario", response_model=ResponseSchema[dict])
async def set_mock_scenario(
    trade_no: str,
    status: str,
    current_user: User = Depends(get_current_user),
):
    """设置模拟支付场景（仅挡板模式）

    用于测试不同支付结果：
    - SUCCESS: 支付成功
    - FAILED: 支付失败
    - TIMEOUT: 支付超时
    """
    if not PaymentAdapterFactory.is_stub_mode():
        raise BadRequestException("当前非挡板模式，无法设置模拟场景")

    try:
        scenario_status = PaymentResultStatus(status)
    except ValueError:
        raise BadRequestException(f"无效的模拟状态: {status}，可选: SUCCESS, FAILED, TIMEOUT")

    stub = get_payment_stub()
    stub.set_scenario(trade_no, scenario_status)

    return ResponseSchema(code=0, data={"trade_no": trade_no, "scenario": status})
