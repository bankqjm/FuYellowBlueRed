"""支付适配层基础架构

提供统一的支付接口抽象，所有支付渠道（微信、银联等）均实现此接口。
通过挡板机制(PaymentStub)在开发/测试环境下模拟支付，不调用真实接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from decimal import Decimal
import time
import uuid


class PaymentResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    TIMEOUT = "TIMEOUT"
    CLOSED = "CLOSED"


@dataclass
class PaymentRequest:
    """统一支付请求"""
    trade_no: str
    amount: Decimal
    subject: str
    body: str = ""
    notify_url: str = ""
    return_url: str = ""
    client_ip: str = ""
    user_id: int = 0
    extra: dict = field(default_factory=dict)


@dataclass
class PaymentResponse:
    """统一支付响应"""
    status: PaymentResultStatus
    trade_no: str
    channel_trade_no: str = ""
    pay_url: str = ""
    qr_code: str = ""
    message: str = ""
    raw_response: dict = field(default_factory=dict)


@dataclass
class PaymentQueryResponse:
    """支付查询响应"""
    status: PaymentResultStatus
    trade_no: str
    channel_trade_no: str = ""
    amount: Decimal = Decimal("0")
    paid_at: str = ""
    message: str = ""
    raw_response: dict = field(default_factory=dict)


@dataclass
class RefundRequest:
    """退款请求"""
    trade_no: str
    refund_no: str
    total_amount: Decimal
    refund_amount: Decimal
    reason: str = ""


@dataclass
class RefundResponse:
    """退款响应"""
    status: PaymentResultStatus
    trade_no: str
    refund_no: str
    channel_refund_no: str = ""
    message: str = ""
    raw_response: dict = field(default_factory=dict)


class PaymentAdapter(ABC):
    """支付适配器抽象基类

    所有支付渠道必须实现此接口。
    """

    @abstractmethod
    def get_channel_name(self) -> str:
        """返回支付渠道名称"""
        ...

    @abstractmethod
    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """创建支付订单"""
        ...

    @abstractmethod
    async def query_payment(self, trade_no: str) -> PaymentQueryResponse:
        """查询支付状态"""
        ...

    @abstractmethod
    async def close_payment(self, trade_no: str) -> bool:
        """关闭支付订单"""
        ...

    @abstractmethod
    async def create_refund(self, request: RefundRequest) -> RefundResponse:
        """创建退款"""
        ...

    @abstractmethod
    async def verify_callback(self, headers: dict, body: dict) -> bool:
        """验证回调签名"""
        ...

    @abstractmethod
    async def parse_callback(self, body: dict) -> dict:
        """解析回调数据"""
        ...


class PaymentStub:
    """支付挡板

    在开发/测试环境下模拟支付行为，不调用真实支付接口。
    支持模拟不同支付场景：成功、失败、超时等。
    """

    def __init__(self, default_status: PaymentResultStatus = PaymentResultStatus.SUCCESS):
        self.default_status = default_status
        self._scenario_overrides: dict[str, PaymentResultStatus] = {}

    def set_scenario(self, trade_no: str, status: PaymentResultStatus):
        """为指定订单设置模拟场景"""
        self._scenario_overrides[trade_no] = status

    def clear_scenario(self, trade_no: str):
        """清除指定订单的模拟场景"""
        self._scenario_overrides.pop(trade_no, None)

    def get_status(self, trade_no: str) -> PaymentResultStatus:
        """获取模拟状态"""
        return self._scenario_overrides.get(trade_no, self.default_status)

    def generate_channel_trade_no(self, channel: str) -> str:
        """生成模拟渠道交易号"""
        prefix = {"WECHAT": "WX", "UNIONPAY": "UP"}.get(channel, "MOCK")
        return f"{prefix}{int(time.time() * 1000)}{uuid.uuid4().hex[:8]}"

    def simulate_payment(self, request: PaymentRequest, channel: str) -> PaymentResponse:
        """模拟支付创建"""
        status = self.get_status(request.trade_no)
        channel_trade_no = self.generate_channel_trade_no(channel)

        if status == PaymentResultStatus.SUCCESS:
            return PaymentResponse(
                status=PaymentResultStatus.SUCCESS,
                trade_no=request.trade_no,
                channel_trade_no=channel_trade_no,
                pay_url=f"mock://{channel.lower()}/pay?trade_no={request.trade_no}",
                qr_code=f"mock://qr/{request.trade_no}",
                message="模拟支付成功",
                raw_response={"mock": True, "channel": channel},
            )
        elif status == PaymentResultStatus.FAILED:
            return PaymentResponse(
                status=PaymentResultStatus.FAILED,
                trade_no=request.trade_no,
                channel_trade_no="",
                message="模拟支付失败",
                raw_response={"mock": True, "channel": channel, "error": "SIMULATED_FAIL"},
            )
        elif status == PaymentResultStatus.TIMEOUT:
            return PaymentResponse(
                status=PaymentResultStatus.TIMEOUT,
                trade_no=request.trade_no,
                channel_trade_no=channel_trade_no,
                pay_url="",
                qr_code="",
                message="模拟支付超时",
                raw_response={"mock": True, "channel": channel, "timeout": True},
            )
        else:
            return PaymentResponse(
                status=status,
                trade_no=request.trade_no,
                channel_trade_no=channel_trade_no,
                message=f"模拟支付状态: {status.value}",
                raw_response={"mock": True, "channel": channel},
            )

    def simulate_query(self, trade_no: str, channel: str) -> PaymentQueryResponse:
        """模拟支付查询"""
        status = self.get_status(trade_no)
        channel_trade_no = self.generate_channel_trade_no(channel)

        return PaymentQueryResponse(
            status=status,
            trade_no=trade_no,
            channel_trade_no=channel_trade_no,
            amount=Decimal("0"),
            paid_at=time.strftime("%Y-%m-%d %H:%M:%S") if status == PaymentResultStatus.SUCCESS else "",
            message=f"模拟查询: {status.value}",
            raw_response={"mock": True, "channel": channel},
        )

    def simulate_refund(self, request: RefundRequest, channel: str) -> RefundResponse:
        """模拟退款"""
        return RefundResponse(
            status=PaymentResultStatus.SUCCESS,
            trade_no=request.trade_no,
            refund_no=request.refund_no,
            channel_refund_no=f"RF{int(time.time() * 1000)}{uuid.uuid4().hex[:6]}",
            message="模拟退款成功",
            raw_response={"mock": True, "channel": channel},
        )


# 全局挡板实例
_payment_stub = PaymentStub()


def get_payment_stub() -> PaymentStub:
    return _payment_stub


class PaymentAdapterFactory:
    """支付适配器工厂

    根据渠道和配置创建对应的支付适配器。
    在 STUB_MODE 下返回挡板适配器，否则返回真实适配器。
    """

    _adapters: dict[str, PaymentAdapter] = {}
    _stub_mode: bool = True

    @classmethod
    def set_stub_mode(cls, enabled: bool):
        cls._stub_mode = enabled

    @classmethod
    def is_stub_mode(cls) -> bool:
        return cls._stub_mode

    @classmethod
    def register(cls, channel: str, adapter: PaymentAdapter):
        cls._adapters[channel] = adapter

    @classmethod
    def get_adapter(cls, channel: str) -> PaymentAdapter:
        adapter = cls._adapters.get(channel)
        if not adapter:
            raise ValueError(f"不支持的支付渠道: {channel}")
        return adapter

    @classmethod
    def get_supported_channels(cls) -> list[str]:
        return list(cls._adapters.keys())
