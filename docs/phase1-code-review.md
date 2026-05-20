# Phase 1 代码审查报告

**审查人**: 高见远 (Gao) · 架构师
**审查日期**: 2026-05-19
**项目**: FuYellowBlueRed 外卖配送平台
**审查范围**: Phase 1 紧急修复（8 项修改）

---

## 总评

| 项目 | 评级 | 说明 |
|------|------|------|
| SEC-REFORM-01: 金额字段 Float → Numeric(10,2) | ⚠️ 需改进 | 模型层正确，但 Schema 层和部分 API 路由存在 Decimal/float 混用遗漏 |
| SEC-REFORM-02: 订单号改用雪花算法 | ✅ 通过 | 实现正确，线程安全，有时钟回拨检测 |
| SEC-REFORM-03: WebSocket JWT 认证 | ⚠️ 需改进 | 核心逻辑正确，但 accept-then-close 模式存在信息泄露风险 |
| API-REFORM-01: require_role 返回 403 | ✅ 通过 | 改动正确，前后端一致 |
| SEC-REFORM-04: 库存扣减加行锁 | ⚠️ 需改进 | order_service 正确，但 shop.py reject_order 缺少行锁 |
| CODE-REFORM-01: API 路由统一调用 Service 层 | ✅ 通过 | orders.py 已完全委托 OrderService |
| U-P0-02: 支付倒计时 + 订单超时自动取消 | ⚠️ 需改进 | 核心逻辑正确，但存在时区不一致和 CountdownTimer 双重触发风险 |
| U-P2-03-FE: 用户钱包前端页面 | ⚠️ 需改进 | 功能完整，但收款账号使用 InputNumber 导致无法输入含字母的账号 |

**IS_PASS: NO** — 存在 1 个必须修复的安全问题和 4 个需改进项

---

## 1. SEC-REFORM-01: 金额字段 Float → Numeric(10,2)

### 1.1 模型层 — ✅ 通过

**文件**: `backend/app/models/models.py`

所有金额字段已正确改为 `Numeric(10, 2)`，非金额字段保留 `Float`：
- ✅ `Wallet.balance`, `Wallet.frozen_balance` → Numeric(10,2)
- ✅ `Shop.min_order_amount`, `Shop.delivery_fee` → Numeric(10,2)
- ✅ `Shop.rating`, `Shop.latitude`, `Shop.longitude` → 保留 Float
- ✅ `Product.price`, `Product.original_price` → Numeric(10,2)
- ✅ `Order.total_amount`, `Order.discount_amount`, `Order.delivery_fee` → Numeric(10,2)
- ✅ `Order.latitude`, `Order.longitude` → 保留 Float
- ✅ `OrderItem.price` → Numeric(10,2)
- ✅ 所有金额字段默认值使用 `Decimal("0.00")` 或 `Decimal("20.00")` 等

### 1.2 Schema 层 — ⚠️ 需改进

**文件**: `backend/app/schemas/base.py`

`DecimalField` 序列化器设计合理：
```python
DecimalField = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(x), return_type=float, when_used="json"),
]
```

**问题**: `order.py` schema 使用了 `DecimalField`，但 `shop.py` 和 `coupons.py` 的 schema 仍使用 `float`：

| 文件 | 字段 | 当前类型 | 应改为 |
|------|------|---------|--------|
| `schemas/shop.py:45` | `ShopInfo.min_order_amount` | `float = 20.0` | `DecimalField` |
| `schemas/shop.py:46` | `ShopInfo.delivery_fee` | `float = 3.0` | `DecimalField` |
| `schemas/shop.py:66` | `ShopDetail.min_order_amount` | `float = 20.0` | `DecimalField` |
| `schemas/shop.py:67` | `ShopDetail.delivery_fee` | `float = 3.0` | `DecimalField` |
| `schemas/shop.py:100` | `ProductCreate.price` | `float` | `Decimal` |
| `schemas/shop.py:101` | `ProductCreate.original_price` | `Optional[float]` | `Optional[Decimal]` |
| `schemas/shop.py:110` | `ProductUpdate.price` | `Optional[float]` | `Optional[Decimal]` |
| `schemas/shop.py:111` | `ProductUpdate.original_price` | `Optional[float]` | `Optional[Decimal]` |
| `schemas/shop.py:123` | `ProductInfo.price` | `float` | `DecimalField` |
| `schemas/shop.py:124` | `ProductInfo.original_price` | `Optional[float]` | `Optional[DecimalField]` |
| `coupons.py:22` (内联) | `CouponResponse.discount_amount` | `float` | `DecimalField` |
| `coupons.py:23` (内联) | `CouponResponse.min_order_amount` | `float` | `DecimalField` |

**影响**: 模型层的 Decimal 精度在 Pydantic 序列化时被丢弃为 float，削弱了 Numeric(10,2) 改造的意义。

### 1.3 Finance Service — ✅ 通过

**文件**: `backend/app/services/finance.py`

- ✅ `to_decimal()` 辅助函数实现合理，处理了 SQLite/aiosqlite 返回 float 的问题
- ✅ 所有金额计算均使用 `to_decimal()` 包装
- ✅ 佣金计算使用 `Decimal.quantize(ZERO, rounding=ROUND_HALF_UP)`
- ✅ 常量使用 `Decimal` 类型：`MAX_SINGLE_RECHARGE`, `MAX_DAILY_RECHARGE`, `MAX_SINGLE_PAYMENT`

**小问题**: `to_decimal()` 在 `finance.py` 和 `order_service.py` 中各定义了一次（代码重复）。建议提取到 `app/utils/decimal.py` 共享。

### 1.4 Order Service — ✅ 通过

**文件**: `backend/app/services/order_service.py`

- ✅ 金额计算全部使用 `to_decimal()` 包装
- ✅ `ZERO = Decimal("0.00")` 常量定义
- ✅ 优惠券金额计算：`min_order_amount = to_decimal(coupon.min_order_amount)`

### 1.5 迁移脚本 — ⚠️ 需改进

**文件**: `backend/alembic/versions/002_change_money_fields_to_numeric.py`

覆盖了 001 迁移中存在的所有金额字段：
- ✅ wallets (balance, frozen_balance)
- ✅ shops (min_order_amount, delivery_fee)
- ✅ products (price, original_price)
- ✅ orders (total_amount, discount_amount, delivery_fee)
- ✅ order_items (price)
- ✅ rider_earnings (amount)
- ✅ withdrawal_records (amount)

**问题**: 001 迁移未包含后续新增的表（coupons, payment_transactions, fund_flows, shop_earnings, platform_commissions, refund_records, finance_audit_logs），这些表由 `create_all()` 自动创建。如果创建时模型仍为 Float，则 002 迁移未覆盖这些表。

**风险级别**: 中。项目使用 SQLite + `create_all()`，当前开发阶段这些表可能已在模型改为 Numeric 后才创建。但生产环境升级时可能遗漏。

**建议**: 新增 003 迁移覆盖所有剩余金额表字段，或确认这些表已在 Numeric 模型下创建。

### 1.6 API 路由 Decimal → float 转换 — ⚠️ 需改进

**wallet.py**: 所有 dict 响应中已正确使用 `float()` 转换 ✅
**rider.py**: 所有 dict 响应中已正确使用 `float()` 转换 ✅
**shop.py**:
- ✅ Line 615, 669: `float()` 转换统计金额
- ⚠️ `ShopInfo.model_validate(shop)` 和 `ProductInfo.model_validate(product)` 依赖 Pydantic 自动转换，但由于 schema 定义为 `float`，Decimal 精度在序列化时丢失

**coupons.py**:
- ⚠️ Line 180-183: `order_amount` (Decimal) 与 `coupon.min_order_amount` (可能为 float) 直接比较，存在类型不一致
- ⚠️ Line 186: `float(discount)` — 使用 `min()` 比较 Decimal 和 float 混合值

**建议**: coupons.py 的 `apply_coupon` 应使用 `to_decimal()` 包装后再比较

---

## 2. SEC-REFORM-02: 订单号改用雪花算法

### 评级: ✅ 通过

**文件**: `backend/app/utils/snowflake.py`

**正确实现**:
- ✅ 标准 Snowflake 结构：1位符号 + 41位时间戳 + 10位机器ID + 12位序列号
- ✅ 线程安全：`threading.Lock()` 保护 `generate_id()`
- ✅ 时钟回拨检测：`RuntimeError` 异常
- ✅ 序列号溢出处理：等待下一毫秒
- ✅ 合理的 epoch 设置（2024-01-01 UTC）
- ✅ 模块级单例模式

**生成函数**:
- ✅ `generate_order_no()` → 返回纯数字字符串，长度 ≤ 19 字符（64位整数），满足 ≤ 32 字符要求
- ✅ `generate_trade_no()` → 返回 "T" + 数字字符串，长度 ≤ 20 字符，满足 PaymentTransaction.trade_no 的 String(64) 约束

**替换完整性**:
- ✅ `order_service.py:244`: `order_no = generate_order_no()`
- ✅ `finance.py:14`: `from app.utils.snowflake import generate_trade_no`
- ✅ `finance.py:40`: `return generate_trade_no()`

**小建议**: 时钟回拨时直接抛异常可能导致服务不可用。生产环境可考虑等待回拨时间过去后继续生成，而非直接失败。

---

## 3. SEC-REFORM-03: WebSocket JWT 认证

### 评级: ⚠️ 需改进

**文件**: `backend/app/main.py:153-221`

**正确实现**:
- ✅ JWT 验证逻辑完整：token 存在性 → 解析验证 → 黑名单检查 → token 类型校验 → user_id 匹配
- ✅ 验证失败返回 4001 状态码
- ✅ 每种失败场景都有安全日志记录（含 channel、user_id 等上下文）
- ✅ 用户 ID 与 token 中的 sub 字段交叉验证，防止 token 冒用

**安全问题 — accept-then-close 模式**:

```python
# 当前实现 (Lines 162-165)
if not token:
    await websocket.accept()       # ← 先接受连接
    await websocket.close(code=4001, reason="Missing token")  # ← 再关闭
```

这个模式存在信息泄露风险：
1. **连接数短暂增加**: 攻击者可大量发起无效 WebSocket 连接，虽然会被关闭，但 `accept()` 消耗服务器资源
2. **reason 信息泄露**: `close()` 的 reason 字段向攻击者透露了具体的验证失败原因

**建议修复**:
```python
# 方案 A: 不 accept，直接拒绝（推荐）
if not token:
    logger.warning(f"WebSocket rejected: no token, channel={channel}, user_id={user_id}")
    await websocket.close(code=4001)  # FastAPI 会在 accept 前关闭
    return

# 方案 B: 如果必须 accept，不要在 reason 中透露具体原因
if not token:
    await websocket.accept()
    await websocket.close(code=4001, reason="Unauthorized")
    return
```

**注意**: FastAPI WebSocket 的 `close()` 在未 `accept()` 前调用的行为取决于 ASGI 服务器实现。需要测试 uvicorn 是否支持方案 A。

---

## 4. API-REFORM-01: require_role 返回 403

### 评级: ✅ 通过

**文件**: `backend/app/deps/auth.py:57-62`

```python
def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException("权限不足")
        return current_user
    return role_checker
```

- ✅ 使用 `ForbiddenException` 返回 403
- ✅ `get_current_user` 仍正确使用 `UnauthorizedException` 返回 401（认证失败）
- ✅ 语义分离清晰：401 = 未认证，403 = 无权限

**文件**: `backend/app/utils/exceptions.py`
- ✅ `ForbiddenException` 返回 `status.HTTP_403_FORBIDDEN`

**文件**: `frontend/src/services/api.ts:30-37`
```typescript
if (status === 401) {
    const { logout } = useAuthStore.getState()
    logout()
    window.location.href = '/login'
    message.error('登录已过期，请重新登录')
} else if (status === 403) {
    message.error('权限不足，无法访问该资源')
}
```
- ✅ 401 触发登出跳转
- ✅ 403 仅显示提示，不登出
- ✅ 全局所有 API 调用统一经过此拦截器

**其他检查**:
- ✅ `admin.py` 中所有权限检查均使用 `ForbiddenException`
- ✅ `rider.py` 中角色检查使用 `ForbiddenException`
- ✅ `shop.py` 中所有权检查使用 `ForbiddenException`
- ✅ 无残留的旧 401 权限不足逻辑

---

## 5. SEC-REFORM-04: 库存扣减加行锁

### 评级: ⚠️ 需改进

**文件**: `backend/app/services/order_service.py`

### create_order — ✅ 通过

```python
# Lines 200-202: 加行锁查询商品
product_result = await self.db.execute(
    select(Product).where(Product.id == cart_item.product_id).with_for_update()
)
# Lines 207-208: 锁后校验库存
if product.stock < cart_item.quantity:
    raise BadRequestException(f"商品 {product.name} 库存不足")
# Lines 273: 扣减库存
product.stock -= quantity
# Lines 276-279: 应用层二次校验（防御 SQLite 忽略 FOR UPDATE）
for product, quantity in order_items:
    if product.stock < 0:
        raise BadRequestException(f"商品 {product.name} 库存不足")
```

- ✅ "Lock → Check → Deduct → Verify" 模式正确
- ✅ 应用层 stock >= 0 校验到位（防御 SQLite 静默忽略 FOR UPDATE）
- ✅ 事务范围合理：整个 create_order 在一个事务中

### cancel_order — ✅ 通过

```python
# Lines 466-468: 还原库存时加行锁
product_result = await self.db.execute(
    select(Product).where(Product.id == item.product_id).with_for_update()
)
# Lines 470-471: 还原
if product:
    product.stock += item.quantity
```

- ✅ 库存还原同样加行锁

### shop.py reject_order — ❌ 必须修复

**文件**: `backend/app/api/v1/shop.py:551-556`

```python
# 缺少 with_for_update()
items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
for item in items_result.scalars().all():
    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = product_result.scalar_one_or_none()
    if product:
        product.stock += item.quantity  # ← 无行锁保护的库存修改
```

**问题**: 商家拒单时还原库存未加 `with_for_update()` 行锁，与 `cancel_order` 的实现不一致。在并发场景下，可能导致库存数据不一致。

**修复建议**:
```python
# shop.py Line 553, 添加 with_for_update()
product_result = await db.execute(
    select(Product).where(Product.id == item.product_id).with_for_update()
)
```

### 优惠券库存 — ⚠️ 需改进

**文件**: `backend/app/api/v1/coupons.py:99`

```python
coupon.remain_count -= 1  # ← 无行锁保护
```

领取优惠券时扣减 `remain_count` 没有 `with_for_update()`，高并发下可能超发。

---

## 6. CODE-REFORM-01: API 路由统一调用 Service 层

### 评级: ✅ 通过

**文件**: `backend/app/api/v1/orders.py`

- ✅ 所有路由方法均只做：参数提取 → 调用 OrderService → 返回 Response
- ✅ 无直接 DB 操作
- ✅ 无业务逻辑遗漏

**OrderService 方法完整性**:

| 方法 | 路由 | 状态 |
|------|------|------|
| `get_cart` | GET /cart | ✅ |
| `add_to_cart` | POST /cart | ✅ |
| `update_cart_item` | PUT /cart/{id} | ✅ |
| `delete_cart_item` | DELETE /cart/{id} | ✅ |
| `clear_shop_cart` | DELETE /cart/shop/{id} | ✅ |
| `create_order` | POST /create | ✅ |
| `pay_order` | POST /{id}/pay | ✅ |
| `get_order_detail` | GET /{id} | ✅ |
| `get_orders` | GET / | ✅ |
| `confirm_receipt` | PUT /{id}/confirm | ✅ |
| `cancel_order` | PUT /{id}/cancel | ✅ |

**其他路由文件**:
- `shop.py`: 仍直接操作 DB，但该文件不在本次改造范围内
- `rider.py`: 仍直接操作 DB，但该文件不在本次改造范围内
- `wallet.py`: 委托 FinanceService，符合规范

---

## 7. U-P0-02: 支付倒计时 + 订单超时自动取消

### 评级: ⚠️ 需改进

### 前端倒计时

**文件**: `frontend/src/pages/user/Orders.tsx`

- ✅ `PAYMENT_TIMEOUT_MS = 15 * 60 * 1000` (15 分钟)
- ✅ `getPaymentDeadline()` 计算截止时间
- ✅ `getRemainingSeconds()` 计算剩余秒数
- ✅ 倒计时归零后调用 `handleCountdownExpire` → `orderApi.cancelOrder()`
- ✅ 列表和支付弹窗均显示倒计时
- ✅ 剩余 ≤ 5 分钟显示红色警告

**CountdownTimer 组件** (`frontend/src/components/CountdownTimer/index.tsx`):
- ✅ 每秒递减
- ✅ 到期触发 `onExpire` 回调
- ⚠️ **双重触发风险**: `useEffect` 中 `remainingSeconds <= 0` 和 `setInterval` 中 `next <= 0` 都会调用 `handleExpire`。如果组件重新渲染导致 effect 重新执行，可能重复触发取消请求。

**修复建议**: 添加防重复触发标志：
```typescript
const expiredRef = useRef(false)
const handleExpire = useCallback(() => {
  if (expiredRef.current) return
  expiredRef.current = true
  onExpire?.()
}, [onExpire])
```

### 后端超时任务

**文件**: `backend/app/tasks/order_timeout.py`

- ✅ Redis 分布式锁实现：`SET NX EX` 原子操作
- ✅ 锁获取失败时跳过（多实例安全）
- ✅ 无 Redis 时降级为单实例模式
- ✅ 异常时释放锁（finally 块）
- ✅ 调用 `OrderService.cancel_order(cancel_type="timeout")`

**时区问题 — ⚠️ 需改进**:

```python
# Line 21: 使用 UTC 时间
cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.timeout_minutes)
# 但 Order.created_at 使用 server_default=func.now()
```

`func.now()` 在 SQLite 中返回本地时间，而 `cutoff_time` 使用 UTC 时间。在非 UTC 时区的服务器上，时间比较可能出错。

**修复建议**: 统一使用 `datetime.now()` 或统一使用 UTC：
```python
cutoff_time = datetime.now() - timedelta(minutes=self.timeout_minutes)
```
或确保模型中 `created_at` 也存储 UTC 时间。

### cancel_order 支持 timeout 类型 — ✅ 通过

`cancel_order` 方法接受 `cancel_type` 和 `reason` 参数，超时任务传入 `cancel_type="timeout"`, `reason="支付超时自动取消"`，逻辑正确。

---

## 8. U-P2-03-FE: 用户钱包前端页面

### 评级: ⚠️ 需改进

### 前端页面

**文件**: `frontend/src/pages/user/Wallet.tsx`

- ✅ 钱包余额展示（渐变背景、大字体）
- ✅ 充值弹窗：金额输入 + 快捷金额 + 提示信息
- ✅ 提现弹窗：仅 SHOP_OWNER/RIDER 可见
- ✅ 交易记录列表：颜色区分收入/支出
- ✅ 分页组件
- ✅ 钱包说明弹窗

**问题 — 提现收款账号使用 InputNumber**:

```tsx
// Line 358-363
<InputNumber
  style={{ width: '100%', marginTop: 8 }}
  placeholder="请输入收款账号"
  value={withdrawAccount ? Number(withdrawAccount) : undefined}
  onChange={(val) => setWithdrawAccount(val ? String(val) : '')}
/>
```

`InputNumber` 只能输入数字，但支付宝/微信账号可能包含字母（如邮箱格式）。应改用 `Input` 组件：

```tsx
<Input
  style={{ width: '100%', marginTop: 8 }}
  placeholder="请输入收款账号"
  value={withdrawAccount}
  onChange={(e) => setWithdrawAccount(e.target.value)}
/>
```

### 前端 API 服务

**文件**: `frontend/src/services/wallet.ts`

- ✅ `getWallet` → GET /wallet
- ✅ `getTransactions` → GET /wallet/transactions
- ✅ `recharge` → POST /wallet/recharge
- ✅ `withdraw` → POST /wallet/withdraw（含 method 和 account 参数）

### 后端新增端点

**文件**: `backend/app/api/v1/wallet.py`

- ✅ `GET /wallet` — 需要 `get_current_user` 依赖
- ✅ `POST /wallet/recharge` — 用户自助充值
- ✅ `POST /wallet/recharge/{user_id}` — 管理员充值，检查 `current_user.role != "ADMIN"`
- ✅ `POST /wallet/withdraw` — 检查角色 `SHOP_OWNER` 或 `RIDER`，验证收款账号非空
- ✅ `GET /wallet/transactions` — 分页查询

**安全问题 — 管理员充值接口**:

```python
# Line 49-53
@router.post("/recharge/{user_id}", response_model=ResponseSchema[dict])
async def admin_recharge_user_wallet(
    user_id: int,
    amount: Decimal = Query(...),  # ← 使用 Query 而非 Body
```

充值金额使用 `Query` 参数而非 `Body`，意味着金额出现在 URL 中。虽然 HTTPS 加密传输，但 URL 可能被记录在：
- 浏览器历史
- 代理服务器日志
- Referer 头

**建议**: 改为 `Body` 参数：
```python
amount: Decimal = Body(..., embed=True)
```

---

## 问题汇总

### ❌ 必须返工

| # | 文件 | 行号 | 问题 | 修复建议 |
|---|------|------|------|---------|
| 1 | `backend/app/api/v1/shop.py` | 553 | reject_order 还原库存缺少 `with_for_update()` 行锁 | 添加 `.with_for_update()` |

### ⚠️ 需改进

| # | 文件 | 行号 | 问题 | 修复建议 |
|---|------|------|------|---------|
| 2 | `backend/app/schemas/shop.py` | 45-46, 66-67, 100-101, 110-111, 123-124 | 金额字段仍使用 `float` 类型 | 改为 `DecimalField` / `Decimal` |
| 3 | `backend/app/api/v1/coupons.py` | 22-23 | CouponResponse 金额字段使用 `float` | 改为 `DecimalField` |
| 4 | `backend/app/api/v1/coupons.py` | 99 | 优惠券 remain_count 扣减无行锁 | 添加 `with_for_update()` |
| 5 | `backend/app/api/v1/coupons.py` | 180-183 | Decimal 与 float 直接比较 | 使用 `to_decimal()` 包装 |
| 6 | `backend/app/main.py` | 162-194 | WebSocket accept-then-close 模式信息泄露 | 不在 close reason 中透露具体原因 |
| 7 | `backend/app/tasks/order_timeout.py` | 21 | 时区不一致：UTC vs 本地时间 | 统一使用 `datetime.now()` 或 UTC |
| 8 | `frontend/src/components/CountdownTimer/index.tsx` | 39-50 | 倒计时到期可能双重触发 onExpire | 添加防重复标志 |
| 9 | `frontend/src/pages/user/Wallet.tsx` | 358-363 | 收款账号使用 InputNumber 无法输入字母 | 改用 Input 组件 |
| 10 | `backend/app/api/v1/wallet.py` | 52 | 管理员充值金额使用 Query 参数 | 改为 Body 参数 |
| 11 | `backend/app/services/finance.py` + `order_service.py` | 23/36 | `to_decimal()` 函数重复定义 | 提取到共享模块 |

### ✅ 通过项

- 模型层 Numeric(10,2) 改造完整
- DecimalField 序列化器设计合理
- 雪花算法实现正确、线程安全
- WebSocket JWT 认证逻辑完整（模式问题见上）
- require_role 正确返回 403，前后端一致
- OrderService 库存扣减行锁 + 应用层校验
- orders.py 完全委托 OrderService
- 超时自动取消任务 Redis 分布式锁正确
- 钱包页面功能完整

---

## 修复优先级建议

| 优先级 | 问题编号 | 说明 |
|--------|---------|------|
| P0 紧急 | #1 | shop.py reject_order 行锁缺失，可能导致库存数据不一致 |
| P1 高 | #2, #3 | Schema 金额字段仍为 float，Decimal 改造不完整 |
| P1 高 | #6 | WebSocket close reason 信息泄露 |
| P1 高 | #7 | 时区不一致可能导致超时判断错误 |
| P2 中 | #4 | 优惠券超发风险 |
| P2 中 | #8 | 倒计时双重触发 |
| P2 中 | #9 | 收款账号无法输入字母 |
| P2 中 | #10 | 充值金额 URL 暴露 |
| P3 低 | #5, #11 | 代码质量改进 |

---

**最终判定: IS_PASS = NO**

存在 1 个必须返工问题（shop.py 行锁缺失）和多个需改进项。建议修复 P0 和 P1 问题后重新审查。
