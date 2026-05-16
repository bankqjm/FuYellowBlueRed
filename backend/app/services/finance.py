import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import (
    Wallet, Order, OrderItem, Shop, User,
    PaymentTransaction, ShopEarning, PlatformCommission,
    FundFlow, RefundRecord,
    TradeType, PayChannel, PaymentStatus,
    AccountType, FlowType, BusinessType,
    SettlementStatus, RefundType, RefundStatus
)
from app.services.config import ConfigService

MAX_SINGLE_RECHARGE = 10000.0
MAX_DAILY_RECHARGE = 50000.0
MAX_SINGLE_PAYMENT = 100000.0


class FinanceService:

    @staticmethod
    def generate_trade_no() -> str:
        return f"TR{uuid.uuid4().hex[:28].upper()}"

    @staticmethod
    async def check_payment_idempotency(db: AsyncSession, order_id: int) -> PaymentTransaction | None:
        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.order_id == order_id,
                PaymentTransaction.trade_type == TradeType.PAY.value,
                PaymentTransaction.status == PaymentStatus.SUCCESS.value
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def ensure_wallet_exists(db: AsyncSession, user_id: int) -> Wallet:
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            wallet = Wallet(user_id=user_id, balance=0.0, frozen_balance=0.0)
            db.add(wallet)
            await db.flush()
        return wallet

    @staticmethod
    async def check_daily_recharge_limit(db: AsyncSession, user_id: int, amount: float) -> tuple[bool, float]:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        result = await db.execute(
            select(func.sum(FundFlow.amount)).where(
                FundFlow.user_id == user_id,
                FundFlow.business_type == BusinessType.RECHARGE.value,
                FundFlow.flow_type == FlowType.INCOME.value,
                FundFlow.created_at >= today_start,
                FundFlow.created_at < today_end
            )
        )
        daily_total = result.scalar() or 0.0

        if daily_total + amount > MAX_DAILY_RECHARGE:
            remaining = MAX_DAILY_RECHARGE - daily_total
            return False, remaining

        return True, daily_total

    @staticmethod
    async def create_fund_flow(
        db: AsyncSession,
        user_id: int,
        account_type: str,
        flow_type: str,
        amount: float,
        business_type: str,
        related_id: int = None,
        description: str = None
    ) -> FundFlow:
        wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = wallet_result.scalar_one_or_none()
        balance_before = wallet.balance if wallet else 0.0
        balance_after = balance_before + amount if flow_type == FlowType.INCOME.value else balance_before - amount

        fund_flow = FundFlow(
            user_id=user_id,
            account_type=account_type,
            flow_type=flow_type,
            amount=abs(amount),
            balance_before=balance_before,
            balance_after=balance_after,
            business_type=business_type,
            related_id=related_id,
            description=description
        )
        db.add(fund_flow)
        await db.flush()
        return fund_flow

    @staticmethod
    async def process_payment(
        db: AsyncSession,
        order: Order,
        user: User,
        channel: str = PayChannel.BALANCE.value
    ) -> dict:
        existing_payment = await FinanceService.check_payment_idempotency(db, order.id)
        if existing_payment:
            return {
                "payment_id": existing_payment.id,
                "trade_no": existing_payment.trade_no,
                "amount": existing_payment.amount,
                "channel": existing_payment.channel,
                "idempotent": True
            }

        if order.total_amount > MAX_SINGLE_PAYMENT:
            raise ValueError(f"单笔支付金额不能超过 {MAX_SINGLE_PAYMENT:.2f} 元")

        wallet = await FinanceService.ensure_wallet_exists(db, user.id)

        if channel == PayChannel.BALANCE.value:
            if wallet.balance < order.total_amount:
                raise ValueError(f"余额不足，当前余额: {wallet.balance:.2f}元")
            wallet.balance -= order.total_amount

        trade_no = FinanceService.generate_trade_no()

        payment = PaymentTransaction(
            order_id=order.id,
            user_id=user.id,
            trade_no=trade_no,
            trade_type=TradeType.PAY.value,
            amount=order.total_amount,
            channel=channel,
            status=PaymentStatus.SUCCESS.value,
            completed_at=datetime.now()
        )
        db.add(payment)
        await db.flush()

        await FinanceService.create_fund_flow(
            db=db,
            user_id=user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.EXPENSE.value,
            amount=order.total_amount,
            business_type=BusinessType.ORDER_PAY.value,
            related_id=order.id,
            description=f"订单支付: {order.order_no}"
        )

        return {
            "payment_id": payment.id,
            "trade_no": trade_no,
            "amount": order.total_amount,
            "channel": channel,
            "idempotent": False
        }

    @staticmethod
    async def calculate_order_commission(db: AsyncSession, order: Order) -> dict:
        goods_amount = order.total_amount - order.delivery_fee

        commission_rate = await ConfigService.get_config_float(
            db, "SHOP_COMMISSION_RATE", 0.10
        )
        shop_commission = round(goods_amount * commission_rate, 2)
        net_amount = round(goods_amount - shop_commission, 2)

        rider_service_rate = await ConfigService.get_config_float(
            db, "RIDER_SERVICE_FEE_RATE", 0.20
        )
        rider_service_fee = round(order.delivery_fee * rider_service_rate, 2)
        rider_income = round(order.delivery_fee - rider_service_fee, 2)

        return {
            "goods_amount": goods_amount,
            "commission_rate": commission_rate,
            "shop_commission": shop_commission,
            "net_amount": net_amount,
            "rider_service_rate": rider_service_rate,
            "rider_service_fee": rider_service_fee,
            "rider_income": rider_income
        }

    @staticmethod
    async def process_order_settlement(db: AsyncSession, order: Order) -> dict:
        commission_info = await FinanceService.calculate_order_commission(db, order)

        shop_earning = ShopEarning(
            shop_id=order.shop_id,
            order_id=order.id,
            order_no=order.order_no,
            goods_amount=commission_info["goods_amount"],
            commission_rate=commission_info["commission_rate"],
            commission_amount=commission_info["shop_commission"],
            net_amount=commission_info["net_amount"],
            status=SettlementStatus.UNSETTLED.value
        )
        db.add(shop_earning)
        await db.flush()

        platform_commission = PlatformCommission(
            order_id=order.id,
            shop_commission=commission_info["shop_commission"],
            rider_service_fee=commission_info["rider_service_fee"],
            total=commission_info["shop_commission"] + commission_info["rider_service_fee"]
        )
        db.add(platform_commission)
        await db.flush()

        return {
            "shop_earning_id": shop_earning.id,
            "platform_commission_id": platform_commission.id,
            "shop_net_amount": commission_info["net_amount"],
            "rider_income": commission_info["rider_income"]
        }

    @staticmethod
    async def check_refund_idempotency(db: AsyncSession, order_id: int) -> RefundRecord | None:
        result = await db.execute(
            select(RefundRecord).where(
                RefundRecord.order_id == order_id,
                RefundRecord.trade_type == TradeType.REFUND.value if hasattr(RefundRecord, 'trade_type') else True,
                RefundRecord.status == RefundStatus.SUCCESS.value
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def process_refund(
        db: AsyncSession,
        order: Order,
        user: User,
        refund_amount: float = None,
        refund_type: str = RefundType.MANUAL.value,
        reason: str = None
    ) -> RefundRecord:
        if refund_amount is None:
            refund_amount = order.total_amount

        payment_result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.trade_type == TradeType.PAY.value,
                PaymentTransaction.status == PaymentStatus.SUCCESS.value
            )
        )
        payment = payment_result.scalar_one_or_none()

        if refund_amount > (payment.amount if payment else order.total_amount):
            raise ValueError("退款金额不能超过实际支付金额")

        wallet = await FinanceService.ensure_wallet_exists(db, user.id)
        wallet.balance += refund_amount

        refund_record = RefundRecord(
            order_id=order.id,
            user_id=user.id,
            transaction_id=payment.id if payment else None,
            refund_amount=refund_amount,
            refund_type=refund_type,
            status=RefundStatus.SUCCESS.value,
            reason=reason,
            processed_at=datetime.now()
        )
        db.add(refund_record)
        await db.flush()

        await FinanceService.create_fund_flow(
            db=db,
            user_id=user.id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=refund_amount,
            business_type=BusinessType.ORDER_REFUND.value,
            related_id=order.id,
            description=f"订单退款: {order.order_no}"
        )

        return refund_record

    @staticmethod
    async def add_rider_earning(
        db: AsyncSession,
        rider_id: int,
        order_id: int,
        amount: float
    ) -> FundFlow:
        wallet = await FinanceService.ensure_wallet_exists(db, rider_id)
        wallet.balance += amount

        fund_flow = await FinanceService.create_fund_flow(
            db=db,
            user_id=rider_id,
            account_type=AccountType.RIDER.value,
            flow_type=FlowType.INCOME.value,
            amount=amount,
            business_type=BusinessType.COMMISSION.value,
            related_id=order_id,
            description=f"配送收入: 订单#{order_id}"
        )

        return fund_flow

    @staticmethod
    async def process_withdrawal(
        db: AsyncSession,
        user_id: int,
        amount: float
    ) -> dict:
        min_withdrawal = await ConfigService.get_config_float(
            db, "MIN_WITHDRAWAL_AMOUNT", 10.0
        )

        if amount < min_withdrawal:
            raise ValueError(f"提现金额不能低于 {min_withdrawal:.2f} 元")

        wallet = await FinanceService.ensure_wallet_exists(db, user_id)

        if wallet.balance < amount:
            raise ValueError(f"余额不足，当前余额: {wallet.balance:.2f}元")

        wallet.balance -= amount

        await FinanceService.create_fund_flow(
            db=db,
            user_id=user_id,
            account_type=AccountType.RIDER.value,
            flow_type=FlowType.EXPENSE.value,
            amount=amount,
            business_type=BusinessType.WITHDRAW.value,
            description=f"提现: {amount:.2f}元"
        )

        return {"amount": amount, "balance_after": wallet.balance}

    @staticmethod
    async def recharge_wallet(
        db: AsyncSession,
        user_id: int,
        amount: float
    ) -> dict:
        if amount <= 0:
            raise ValueError("充值金额必须大于0")

        if amount > MAX_SINGLE_RECHARGE:
            raise ValueError(f"单笔充值金额不能超过 {MAX_SINGLE_RECHARGE:.2f} 元")

        within_limit, daily_total = await FinanceService.check_daily_recharge_limit(db, user_id, amount)
        if not within_limit:
            raise ValueError(f"今日充值总额已达上限，剩余可用额度: {daily_total:.2f} 元")

        wallet = await FinanceService.ensure_wallet_exists(db, user_id)
        wallet.balance += amount

        await FinanceService.create_fund_flow(
            db=db,
            user_id=user_id,
            account_type=AccountType.USER.value,
            flow_type=FlowType.INCOME.value,
            amount=amount,
            business_type=BusinessType.RECHARGE.value,
            description=f"钱包充值: {amount:.2f}元"
        )

        return {
            "amount": amount,
            "balance": wallet.balance,
            "daily_total": daily_total + amount
        }
