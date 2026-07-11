"""微信支付适配层

实现微信支付V3接口规范，包括：
- 请求参数组装（JSAPI/APP/H5/Native）
- 签名生成（HMAC-SHA256）
- 响应解析
- 回调验证

在挡板模式下，所有操作由 PaymentStub 模拟，不调用真实接口。
"""

import hashlib
import hmac
import json
import time
import uuid
from typing import Optional

from .base import (
    PaymentAdapter, PaymentRequest, PaymentResponse,
    PaymentQueryResponse, RefundRequest, RefundResponse,
    PaymentResultStatus, PaymentAdapterFactory, get_payment_stub,
)


class WechatPayConfig:
    """微信支付配置"""

    def __init__(
        self,
        app_id: str = "",
        mch_id: str = "",
        api_key: str = "",
        cert_path: str = "",
        notify_url: str = "",
    ):
        self.app_id = app_id or "wx_mock_app_id"
        self.mch_id = mch_id or "1900000000"
        self.api_key = api_key or "mock_api_key_32_characters_long!!"
        self.cert_path = cert_path
        self.notify_url = notify_url or "https://mock.example.com/api/v1/payment/callback/wechat"


class WechatPayAdapter(PaymentAdapter):
    """微信支付适配器

    实现微信支付V3接口规范。
    在挡板模式下通过 PaymentStub 模拟所有操作。
    """

    CHANNEL = "WECHAT"

    def __init__(self, config: Optional[WechatPayConfig] = None):
        self.config = config or WechatPayConfig()
        self._stub = get_payment_stub()

    def get_channel_name(self) -> str:
        return "微信支付"

    def _build_request_params(self, request: PaymentRequest) -> dict:
        """组装微信支付请求参数（V3规范）"""
        params = {
            "appid": self.config.app_id,
            "mch_id": self.config.mch_id,
            "nonce_str": uuid.uuid4().hex[:32],
            "sign_type": "HMAC-SHA256",
            "body": request.subject,
            "detail": request.body or request.subject,
            "out_trade_no": request.trade_no,
            "total_fee": int(request.amount * 100),  # 微信支付金额单位为分
            "spbill_create_ip": request.client_ip or "127.0.0.1",
            "notify_url": request.notify_url or self.config.notify_url,
            "trade_type": "NATIVE",  # 默认Native扫码支付
            "time_start": time.strftime("%Y%m%d%H%M%S"),
            "time_expire": time.strftime(
                "%Y%m%d%H%M%S",
                time.localtime(time.time() + 1800)  # 30分钟过期
            ),
        }
        if request.extra.get("openid"):
            params["openid"] = request.extra["openid"]
            params["trade_type"] = "JSAPI"
        if request.extra.get("trade_type"):
            params["trade_type"] = request.extra["trade_type"]

        return params

    def _generate_signature(self, params: dict) -> str:
        """生成微信支付签名（HMAC-SHA256）

        签名规则：
        1. 按字典序排序所有非空参数
        2. 拼接成 key=value&key=value 格式
        3. 末尾拼接 &key=API_KEY
        4. 进行 HMAC-SHA256 运算
        """
        filtered = {k: v for k, v in params.items() if v is not None and v != ""}
        sorted_keys = sorted(filtered.keys())
        sign_str = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
        sign_str += f"&key={self.config.api_key}"

        signature = hmac.new(
            self.config.api_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()
        return signature

    def _parse_response(self, response_data: dict) -> PaymentResponse:
        """解析微信支付响应"""
        return_code = response_data.get("return_code", "FAIL")
        result_code = response_data.get("result_code", "FAIL")

        if return_code == "SUCCESS" and result_code == "SUCCESS":
            return PaymentResponse(
                status=PaymentResultStatus.SUCCESS,
                trade_no=response_data.get("out_trade_no", ""),
                channel_trade_no=response_data.get("transaction_id", ""),
                pay_url=response_data.get("code_url", ""),
                qr_code=response_data.get("code_url", ""),
                message="支付成功",
                raw_response=response_data,
            )
        elif return_code == "SUCCESS" and result_code == "FAIL":
            return PaymentResponse(
                status=PaymentResultStatus.FAILED,
                trade_no=response_data.get("out_trade_no", ""),
                message=response_data.get("err_code_des", "支付失败"),
                raw_response=response_data,
            )
        else:
            return PaymentResponse(
                status=PaymentResultStatus.FAILED,
                trade_no="",
                message=response_data.get("return_msg", "通信失败"),
                raw_response=response_data,
            )

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """创建微信支付订单"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_payment(request, self.CHANNEL)

        # 真实接口调用（挡板模式下不执行）
        params = self._build_request_params(request)
        params["sign"] = self._generate_signature(params)
        # TODO: 实际调用微信支付API
        # response = await httpx_client.post(WECHAT_PAY_URL, data=xml.dumps(params))
        # return self._parse_response(response)
        raise NotImplementedError("真实微信支付接口未实现，请使用挡板模式")

    async def query_payment(self, trade_no: str) -> PaymentQueryResponse:
        """查询微信支付状态"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_query(trade_no, self.CHANNEL)

        raise NotImplementedError("真实微信支付查询接口未实现，请使用挡板模式")

    async def close_payment(self, trade_no: str) -> bool:
        """关闭微信支付订单"""
        if PaymentAdapterFactory.is_stub_mode():
            return True
        raise NotImplementedError("真实微信支付关闭接口未实现，请使用挡板模式")

    async def create_refund(self, request: RefundRequest) -> RefundResponse:
        """创建微信退款"""
        if PaymentAdapterFactory.is_stub_mode():
            return self._stub.simulate_refund(request, self.CHANNEL)

        raise NotImplementedError("真实微信退款接口未实现，请使用挡板模式")

    async def verify_callback(self, headers: dict, body: dict) -> bool:
        """验证微信支付回调签名

        微信V3使用HTTP头中的签名信息验证：
        - Wechatpay-Timestamp: 时间戳
        - Wechatpay-Nonce: 随机串
        - Wechatpay-Signature: 签名
        - Wechatpay-Serial: 证书序列号
        """
        if PaymentAdapterFactory.is_stub_mode():
            return True

        timestamp = headers.get("Wechatpay-Timestamp", "")
        nonce = headers.get("Wechatpay-Nonce", "")
        signature = headers.get("Wechatpay-Signature", "")

        if not all([timestamp, nonce, signature]):
            return False

        # 构造验签串
        sign_str = f"{timestamp}\n{nonce}\n{json.dumps(body, separators=(',', ':'))}\n"
        expected_sig = hmac.new(
            self.config.api_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    async def parse_callback(self, body: dict) -> dict:
        """解析微信支付回调数据"""
        if PaymentAdapterFactory.is_stub_mode():
            return {
                "trade_no": body.get("out_trade_no", ""),
                "channel_trade_no": body.get("transaction_id", ""),
                "status": PaymentResultStatus.SUCCESS if body.get("result_code") == "SUCCESS" else PaymentResultStatus.FAILED,
                "amount": Decimal(str(body.get("total_fee", 0))) / 100,
            }

        result_code = body.get("result_code", "")
        return {
            "trade_no": body.get("out_trade_no", ""),
            "channel_trade_no": body.get("transaction_id", ""),
            "status": PaymentResultStatus.SUCCESS if result_code == "SUCCESS" else PaymentResultStatus.FAILED,
            "amount": Decimal(str(body.get("total_fee", 0))) / 100,
        }


from decimal import Decimal  # noqa: E402 - needed for parse_callback
