import uuid
from datetime import datetime
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


class FinanceService:

    @staticmethod
    def generate_trade_no() -> str:
        return f"TR{uuid.uuid4().hex[:28].upper()}"

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
        return fund_flow

    @staticmethod
    async def process_payment(
        db: AsyncSession,
        order: Order,
        user: User,
        channel: str = PayChannel.BALANCE.value
    ) -> dict:
        wallet = await FinanceService.ensure_wallet_exists(db, user.id)

        if channel == PayChannel.BALANCE.value:
            if wallet.balance < order.total_amount:
                raise ValueError(f"余额不足，当前余额: {wallet.balance:.2f}元")
            wallet.balance -= order.total_amount

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

        payment = PaymentTransaction(
            order_id=order.id,
            user_id=user.id,
            trade_no=FinanceService.generate_trade_no(),
            trade_type=TradeType.PAY.value,
            amount=order.total_amount,
            channel=channel,
            status=PaymentStatus.SUCCESS.value,
            completed_at=datetime.now()
        )
        db.add(payment)

        return {
            "payment_id": payment.id,
            "trade_no": payment.trade_no,
            "amount": order.total_amount,
            "channel": channel
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

        platform_commission = PlatformCommission(
            order_id=order.id,
            shop_commission=commission_info["shop_commission"],
            rider_service_fee=commission_info["rider_service_fee"],
            total=commission_info["shop_commission"] + commission_info["rider_service_fee"]
        )
        db.add(platform_commission)

        return {
            "shop_earning_id": shop_earning.id,
            "platform_commission_id": platform_commission.id,
            "shop_net_amount": commission_info["net_amount"],
            "rider_income": commission_info["rider_income"]
        }

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

        wallet = await FinanceService.ensure_wallet_exists(db, user.id)
        wallet.balance += refund_amount

        payment_result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.trade_type == TradeType.PAY.value,
                PaymentTransaction.status == PaymentStatus.SUCCESS.value
            )
        )
        payment = payment_result.scalar_one_or_none()

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
