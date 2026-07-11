"""支付模块

提供统一的支付服务，支持微信支付和银联云闪付。
通过挡板机制在开发/测试环境下模拟支付。
"""

from .base import (
    PaymentAdapter,
    PaymentRequest,
    PaymentResponse,
    PaymentQueryResponse,
    RefundRequest,
    RefundResponse,
    PaymentResultStatus,
    PaymentStub,
    PaymentAdapterFactory,
    get_payment_stub,
)
from .wechat import WechatPayAdapter, WechatPayConfig
from .unionpay import UnionPayAdapter, UnionPayConfig


def init_payment_adapters():
    """初始化支付适配器

    注册所有支持的支付渠道到工厂。
    默认启用挡板模式。
    """
    PaymentAdapterFactory.set_stub_mode(True)
    PaymentAdapterFactory.register("WECHAT", WechatPayAdapter())
    PaymentAdapterFactory.register("UNIONPAY", UnionPayAdapter())


__all__ = [
    "PaymentAdapter",
    "PaymentRequest",
    "PaymentResponse",
    "PaymentQueryResponse",
    "RefundRequest",
    "RefundResponse",
    "PaymentResultStatus",
    "PaymentStub",
    "PaymentAdapterFactory",
    "get_payment_stub",
    "WechatPayAdapter",
    "WechatPayConfig",
    "UnionPayAdapter",
    "UnionPayConfig",
    "init_payment_adapters",
]
