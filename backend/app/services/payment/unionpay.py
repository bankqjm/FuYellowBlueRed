"""银联云闪付适配层

实现银联全渠道支付接口规范，包括：
- 请求参数组装（手机控件/PC网页/QR码）
- 签名生成（SHA256WithRSA）
- 响应解析与验签
- 回调通知处理

在挡板模式下，所有操作由 PaymentStub 模拟，不调用真实接口。
"""

import hashlib
import json
import time
import uuid
from typing import Optional

from .base import (
    PaymentAdapter, PaymentRequest, PaymentResponse,
    PaymentQueryResponse, RefundRequest, RefundResponse,
    PaymentResultStatus, PaymentAdapterFactory, get_payment_stub,
)


class UnionPayConfig:
    """银联支付配置"""

    def __init__(
        self,
        mer_id: str = "",
        cert_path: str = "",
        cert_password: str = "",
        front_url: str = "",
        back_url: str = "",
        env: str = "test",
    ):
        self.mer_id = mer_id or "777290058110097"
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.front_url = front_url or "https://mock.example.com/payment/unionpay/front"
        self.back_url = back_url or "https://mock.example.com/api/v1/payment/callback/unionpay"
        self.env = env  # test | production
        self.api_url = (
            "https://gateway.test.95516.com"
            if env == "test"
            else "https://gateway.95516.com"
        )


class UnionPayAdapter(PaymentAdapter):
    """银联云闪付适配器

    实现银联全渠道支付接口规范。
    在挡板模式下通过 PaymentStub 模拟所有操作。
    """

    CHANNEL = "UNIONPAY"

    def __init__(self, config: Optional[UnionPayConfig] = None):
        self.config = config or UnionPayConfig()
        self._stub = get_payment_stub()

    def get_channel_name(self) -> str:
        return "银联云闪付"

    def _build_request_params(self, request: PaymentRequest) -> dict:
        """组装银联支付请求参数

        银联全渠道支付接口参数规范：
        - version: 接口版本 5.1.0
        - encoding: 编码 UTF-8
        - signMethod: 签名方法 SHA256
        - txnType: 交易类型 01-消费
        - txnSubType: 交易子类型 01-自助消费
        - bizType: 业务类型 000201
        - channelType: 渠道类型 07-PC 08-移动
        """
        params = {
            "version": "5.1.0",
            "encoding": "UTF-8",
            "signMethod": "01",  # RSA
            "txnType": "01",
            "txnSubType": "01",
            "bizType": "000201",
            "channelType": request.extra.get("channel_type", "07"),
            "merId": self.config.mer_id,
            "orderId": request.trade_no,
            "txnTime": time.strftime("%Y%m%d%H%M%S"),
            "txnAmt": str(int(request.amount * 100)),  # 银联金额单位为分
            "currencyCode": "156",  # 人民币
            "frontUrl": request.return_url or self.config.front_url,
            "backUrl": request.notify_url or self.config.back_url,
            "reqReserved": request.subject,
        }

        if request.extra.get("acc_no"):
            # 银联云闪付控件支付需要卡号（加密）
            params["accType"] = "01"
            params["accNo"] = request.extra["accNo"]

        return params

    def _generate_signature(self, params: dict) -> str:
        """生成银联支付签名

        银联签名规则（SHA256WithRSA）：
        1. 按字典序排序所有非空参数（排除sign字段）
        2. 拼接成 key=value&key=value 格式
        3. 使用商户私钥进行SHA256WithRSA签名
        4. 签名结果Base64编码

        挡板模式下使用模拟签名。
        """
        filtered = {k: v for k, v in params.items()
                     if v is not None and v != "" and k != "signature"}
        sorted_keys = sorted(filtered.keys())
        sign_str = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)

        # 挡板模式：使用SHA256哈希模拟签名
        mock_sig = hashlib.sha256(
            (sign_str + self.config.mer_id).encode("utf-8")
        ).hexdigest().upper()
        return mock_sig

    def _verify_signature(self, params: dict, signature: str) -> bool:
        """验证银联响应签名

        使用银联公钥验证签名。
        挡板模式下直接返回True。
        """
        if PaymentAdapterFactory.is_stub_mode():
            return True

        # TODO: 使用银联公钥证书验证签名
        # 1. 从params中取出signature字段
        # 2. 按字典序排序其余参数
        # 3. 使用银联公钥验证SHA256WithRSA签名
        return True

    def _parse_response(self, response_data: dict) -> PaymentResponse:
        """解析银联支付响应"""
        resp_code = response_data.get("respCode", "")
        resp_msg = response_data.get("respMsg", "")

        if resp_code == "00":
            return PaymentResponse(
                status=PaymentResultStatus.SUCCESS,
                trade_no=response_data.get("orderId", ""),
                channel_trade_no=response_data.get("queryId", ""),
                pay_url=response_data.get("tn", ""),  # 银联交易流水号用于跳转
                qr_code=response_data.get("qrCode", ""),
                message="支付成功",
                raw_response=response_data,
            )
        elif resp_code in ("03", "04", "05"):
            # 03-商户权限不足 04-格式错误 05-认证失败
            return PaymentResponse(
                status=PaymentResultStatus.FAILED,
                trade_no=response_data.get("orderId", ""),
                message=f"支付失败: {resp_msg}",
                raw_response=response_data,
            )
        else:
            return PaymentResponse(
                status=PaymentResultStatus.PENDING,
                trade_no=response_data.get("orderId", ""),
                message=f"支付处理中: {resp_msg}",
                raw_response=response_data,
            )

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """创建银联支付订单"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_payment(request, self.CHANNEL)

        params = self._build_request_params(request)
        params["signature"] = self._generate_signature(params)
        # TODO: 实际调用银联支付API
        # response = await httpx_client.post(self.config.api_url, data=params)
        # return self._parse_response(response)
        raise NotImplementedError("真实银联支付接口未实现，请使用挡板模式")

    async def query_payment(self, trade_no: str) -> PaymentQueryResponse:
        """查询银联支付状态"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_query(trade_no, self.CHANNEL)

        raise NotImplementedError("真实银联查询接口未实现，请使用挡板模式")

    async def close_payment(self, trade_no: str) -> bool:
        """关闭银联支付订单（银联使用撤销/退货接口）"""
        if PaymentAdapterFactory.is_stub_mode():
            return True
        raise NotImplementedError("真实银联关闭接口未实现，请使用挡板模式")

    async def create_refund(self, request: RefundRequest) -> RefundResponse:
        """创建银联退款"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_refund(request, self.CHANNEL)

        raise NotImplementedError("真实银联退款接口未实现，请使用挡板模式")

    async def verify_callback(self, headers: dict, body: dict) -> bool:
        """验证银联支付回调签名

        银联回调签名验证：
        1. 从body中取出signature字段
        2. 按字典序排序其余参数
        3. 使用银联公钥验证SHA256WithRSA签名
        """
        if PaymentAdapterFactory.is_stub_mode():
            return True

        signature = body.get("signature", "")
        if not signature:
            return False

        return self._verify_signature(body, signature)

    async def parse_callback(self, body: dict) -> dict:
        """解析银联支付回调数据"""
        resp_code = body.get("respCode", "")
        return {
            "trade_no": body.get("orderId", ""),
            "channel_trade_no": body.get("queryId", ""),
            "status": PaymentResultStatus.SUCCESS if resp_code == "00" else PaymentResultStatus.FAILED,
            "amount": Decimal(str(body.get("txnAmt", 0))) / 100,
            "currency": body.get("currencyCode", "156"),
        }


from decimal import Decimal  # noqa: E402
