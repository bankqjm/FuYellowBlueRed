# Phase 2 代码审查报告

**审查人**: 高见远 (Gao) · 架构师
**审查日期**: 2026-05-19
**项目**: FuYellowBlueRed 外卖配送平台
**审查范围**: Phase 2 全部修改（11 项）

---

## 总评

| 项目 | 评级 | 说明 |
|------|------|------|
| SEC-REFORM-05: HttpOnly Cookie + CSRF | ✅ 通过 | Double Submit Cookie 实现正确，前后端配合完整 |
| SEC-REFORM-07: XSS 防护 | ⚠️ 需改进 | bleach 使用正确，但 coupons.py 的 CouponResponse 仍用 float 未用 DecimalField |
| SEC-REFORM-08: 敏感日志脱敏 | ⚠️ 需改进 | 核心日志已脱敏，但 audit.py 金额日志未脱敏 |
| SEC-REFORM-06: 密码强度 + 限流完善 | ✅ 通过 | 密码强度校验和可配置限流参数实现完整 |
| PERF-REFORM-01: N+1 查询修复 | ✅ 通过 | 批量 IN 查询替换正确，未引入新问题 |
| PERF-REFORM-02: Redis 缓存层 | ✅ 通过 | 容错设计合理，TTL 设置适当，但缓存失效策略不完整 |
| PERF-REFORM-03: 前端路由懒加载 | ✅ 通过 | React.lazy 配置正确，Suspense fallback 合理 |
| UX-REFORM-02: 管理员订单管理增强 | ⚠️ 需改进 | 搜索和导出功能完整，但 admin 订单详情页未脱敏手机号 |
| UX-REFORM-01: 图片上传验收 | ✅ 通过 | Review.tsx 和 Products.tsx 图片上传集成完整 |
| TEST-REFORM-01: 并发+边界测试 | ⚠️ 需改进 | 测试覆盖面合理，但并发测试实际为串行执行 |

**IS_PASS: NO** — 存在 1 个必须返工的安全问题（audit.py 金额未脱敏）和若干需改进项

---

## 1. SEC-REFORM-05: HttpOnly Cookie + CSRF

### 评级: ✅ 通过

### CSRF 中间件 (`backend/app/core/csrf_middleware.py`)

- ✅ Double Submit Cookie 模式实现正确
- ✅ 正确跳过安全方法（GET, HEAD, OPTIONS）
- ✅ 正确跳过 WebSocket 升级请求
- ✅ DEBUG 模式下跳过验证（开发便利性）
- ✅ Cookie 缺失和 Token 不匹配分别记录日志
- ✅ 验证失败返回 403 + `CSRF_FAILED` error_code

### 前端 CSRF 集成 (`frontend/src/services/api.ts`)

- ✅ `getCsrfTokenFromCookie()` 正确从非 HttpOnly cookie 读取 csrf_token
- ✅ 请求拦截器对 POST/PUT/DELETE/PATCH 自动注入 `X-CSRF-Token` header
- ✅ 响应拦截器区分 `CSRF_FAILED` 和普通 403，给用户不同提示

### Auth 端点 (`backend/app/api/v1/auth.py`)

- ✅ Login: 设置 `access_token`（HttpOnly）、`refresh_token`（HttpOnly）、`csrf_token`（非 HttpOnly）三个 cookie
- ✅ Cookie 属性正确：`httponly=True/False`、`secure=!DEBUG`、`samesite=lax`
- ✅ Refresh: 同时刷新 CSRF token
- ✅ Logout: 清除所有三个 cookie
- ✅ CSRF token 使用 `secrets.token_hex(32)` 生成（64 字符 hex，安全强度足够）

### 中间件注册顺序 (`backend/app/main.py:107-117`)

```python
app.add_middleware(CORSMiddleware, ...)    # 1. CORS
app.add_middleware(RequestLoggingMiddleware)  # 2. 日志
app.add_middleware(SecurityHeadersMiddleware)  # 3. 安全头
app.add_middleware(CSRFMiddleware)            # 4. CSRF
```

⚠️ **注意**: Starlette 中间件执行顺序是**反向的**（最后注册的最先执行）。这意味着请求进入时：CSRF → SecurityHeaders → RequestLogging → CORS。CSRF 在 CORS 之前执行，理论上没有问题，因为 CSRF 不依赖 CORS 处理。但如果 CORS 预检请求（OPTIONS）被 CSRF 拦截，可能导致跨域请求失败。

**验证**: CSRF 中间件已正确跳过 OPTIONS 方法（Line 32: `if request.method in SAFE_METHODS`），所以不存在问题。

---

## 2. SEC-REFORM-07: XSS 防护

### 评级: ⚠️ 需改进

### Sanitizer 工具 (`backend/app/utils/sanitizer.py`)

- ✅ `strip_all_tags()`: 使用 `bleach.clean(tags=[])` 完全去除 HTML，适用于纯文本字段
- ✅ `sanitize_limited_html()`: 允许安全格式标签（p, br, b, i, strong, em, ul, ol, li），无属性
- ✅ `strip_dangerous_content()`: 移除危险标签但保留安全格式
- ✅ 所有函数都有 None/空值保护
- ⚠️ `DENIED_PROTOCOLS` 常量定义了但未使用（bleach 默认已过滤 javascript: 协议）

### Schema 验证器覆盖

| Schema | 字段 | 清理函数 | 状态 |
|--------|------|---------|------|
| `auth.py:RegisterRequest` | nickname | strip_all_tags | ✅ |
| `auth.py:RegisterRequest` | password | 无（无需清理） | ✅ |
| `auth.py:UpdateUserRequest` | nickname | strip_all_tags | ✅ |
| `order.py:OrderCreate` | remark | strip_all_tags | ✅ |
| `review.py:ReviewCreate` | content | strip_all_tags | ✅ |
| `shop.py:ShopCreate` | name | strip_dangerous_content | ✅ |
| `shop.py:ShopCreate` | notice | sanitize_limited_html | ✅ |
| `shop.py:ShopUpdate` | name | strip_dangerous_content | ✅ |
| `shop.py:ShopUpdate` | notice | sanitize_limited_html | ✅ |
| `shop.py:ProductCreate` | name | strip_dangerous_content | ✅ |
| `shop.py:ProductCreate` | description | sanitize_limited_html | ✅ |
| `shop.py:ProductUpdate` | name | strip_dangerous_content | ✅ |
| `shop.py:ProductUpdate` | description | sanitize_limited_html | ✅ |

### 遗漏的输入字段

| 字段 | 位置 | 当前状态 | 建议 |
|------|------|---------|------|
| `ReviewCreate.images` | `schemas/review.py:13` | `List[str]`（URL 列表） | ⚠️ URL 字段应验证格式，防止 `javascript:` 协议 |
| `ShopCreate.logo` | `schemas/shop.py:12` | `Optional[str]` | ⚠️ 应验证 URL 格式 |
| `ProductCreate.image` | `schemas/shop.py:131` | `Optional[str]` | ⚠️ 应验证 URL 格式 |
| `RegisterRequest.phone` | `schemas/auth.py:9` | 有正则验证 | ✅ |
| `UserAddress.address` | 无独立 schema | — | ⚠️ 地址字段未做 XSS 清理 |

**风险级别**: 中。图片 URL 字段如果被注入 `javascript:alert(1)` 或 `data:text/html,...` 等协议，在前端 `<img src="...">` 中通常不会执行，但在 `<a href="...">` 中可能被利用。

---

## 3. SEC-REFORM-08: 敏感日志脱敏

### 评级: ⚠️ 需改进

### 脱敏工具 (`backend/app/utils/log_mask.py`)

5 种脱敏规则：
- ✅ `mask_phone`: 138****5678（保留前3后4）
- ✅ `mask_amount`: 128.**（隐藏小数部分）
- ✅ `mask_id_card`: 110***************234（保留前3后4）
- ✅ `mask_bank_card`: ****1234（仅保留后4）
- ✅ `mask_email`: t***r@example.com（保留首尾字符）
- ✅ `mask_phone_in_text`: 正则替换文本中的手机号

### 已脱敏的日志

| 文件 | 日志 | 脱敏方式 | 状态 |
|------|------|---------|------|
| `auth.py:25` | 注册手机号 | mask_phone | ✅ |
| `auth.py:31` | 已注册手机号 | mask_phone | ✅ |
| `auth.py:59` | 登录手机号 | mask_phone | ✅ |
| `auth.py:74` | 不存在手机号 | mask_phone | ✅ |
| `wallet.py:66` | 充值金额 | mask_amount | ✅ |
| `wallet.py:91` | 自助充值金额 | mask_amount | ✅ |
| `wallet.py:134` | 提现金额 | mask_amount | ✅ |
| `rider.py:170` | 骑手收入金额 | mask_amount | ✅ |
| `rider.py:271` | 骑手提现金额 | mask_amount | ✅ |
| `admin.py:345` | 用户手机号 | mask_phone | ✅ |

### ❌ 必须返工：audit.py 金额未脱敏

**文件**: `backend/app/services/audit.py:51`

```python
logger.warning(f"Large amount alert: user_id={user_id}, type={audit_type}, amount={amount}")
```

**问题**: 大额交易告警日志中直接输出了原始金额，未使用 `mask_amount()` 脱敏。这违反了 SEC-REFORM-08 的要求，且大额交易正是最需要脱敏的场景。

**修复**:
```python
from app.utils.log_mask import mask_amount
logger.warning(f"Large amount alert: user_id={user_id}, type={audit_type}, amount={mask_amount(amount)}")
```

### 其他遗漏

| 文件 | 日志 | 问题 |
|------|------|------|
| `finance.py:146` | `余额不足，当前余额: {to_decimal(wallet.balance):.2f}元` | ⚠️ ValueError 消息中包含原始余额，但此消息会返回给用户而非记录到日志，可接受 |
| `finance.py:350` | 同上 | ⚠️ 同上 |

---

## 4. SEC-REFORM-06: 密码强度 + 限流完善

### 评级: ✅ 通过

### 密码强度校验 (`schemas/auth.py:22-33`)

```python
@field_validator("password")
@classmethod
def validate_password_strength(cls, v: str) -> str:
    if len(v) < 8: raise ValueError("密码长度至少8位")
    if not re.search(r"[a-z]", v): raise ValueError("密码必须包含小写字母")
    if not re.search(r"[A-Z]", v): raise ValueError("密码必须包含大写字母")
    if not re.search(r"\d", v): raise ValueError("密码必须包含数字")
    return v
```

- ✅ 最小长度 8 位
- ✅ 必须包含小写字母、大写字母、数字
- ✅ 确认密码一致性校验
- ✅ 使用 Pydantic `field_validator` 在 Schema 层验证

### 限流参数可配置 (`auth.py:62-68`)

```python
from app.services.config import ConfigService
max_login_attempts = await ConfigService.get_config_int(
    db, "MAX_LOGIN_ATTEMPTS", DEFAULT_MAX_LOGIN_ATTEMPTS
)
lock_duration_minutes = await ConfigService.get_config_int(
    db, "LOCK_DURATION_MINUTES", DEFAULT_LOCK_DURATION_MINUTES
)
```

- ✅ 从 PlatformConfig 读取配置
- ✅ 有合理的默认值（5 次尝试，15 分钟锁定）
- ✅ `get_config_int()` 实现正确（`services/config.py:38-45`）

### 小问题

- ⚠️ `MAX_LOGIN_ATTEMPTS` 和 `LOCK_DURATION_MINUTES` 未在 `DEFAULT_CONFIGS` 中定义默认值，首次运行时 `get_config_int` 会使用代码中的硬编码默认值。建议添加到 `DEFAULT_CONFIGS`。

---

## 5. PERF-REFORM-01: N+1 查询修复

### 评级: ✅ 通过

### order_service.py — get_cart

**修复前**: 每个购物车项单独查询 Product 和 Shop（2N+1 查询）
**修复后**: 批量 IN 查询（3 查询）

```python
# Line 62-74
product_ids = list({item.product_id for item in cart_items})
shop_ids = list({item.shop_id for item in cart_items})
products_result = await self.db.execute(select(Product).where(Product.id.in_(product_ids)))
product_map = {p.id: p for p in products_result.scalars().all()}
shops_result = await self.db.execute(select(Shop).where(Shop.id.in_(shop_ids)))
shop_map = {s.id: s for s in shops_result.scalars().all()}
```

- ✅ 正确使用 `set` 去重 ID 列表
- ✅ 使用 `dict` 建立 ID → 对象映射
- ✅ 空列表保护（Line 59: `if not cart_items: return []`）

### order_service.py — get_orders

**修复前**: 每个订单单独查询 Shop 和 OrderItem（2N+1 查询）
**修复后**: 批量 IN 查询（4 查询）

- ✅ 批量查询 Shop 和 OrderItem
- ✅ `items_by_order` 使用 dict 按 order_id 分组
- ✅ 空结果提前返回

### order_service.py — cancel_order

**修复前**: 每个订单项单独查询 Product（N+1 查询）
**修复后**: 批量 IN 查询 + with_for_update()

```python
# Line 498-511
product_ids = [item.product_id for item in order_items]
if product_ids:
    products_result = await self.db.execute(
        select(Product).where(Product.id.in_(product_ids)).with_for_update()
    )
    product_map = {p.id: p for p in products_result.scalars().all()}
```

- ✅ 批量行锁查询，合并为一条 `SELECT ... FOR UPDATE WHERE id IN (...)`
- ✅ 正确处理空列表（`if product_ids:`）

### admin.py — list_all_orders

**修复前**: 每个订单单独查询 Shop 和 User（2N+1 查询）
**修复后**: 批量 IN 查询（4 查询）

- ✅ 批量查询 Shop 和 User
- ✅ 用户手机号使用 `mask_phone()` 脱敏

### review.py — get_shop_reviews

**修复前**: 每条评价单独查询 User（N+1 查询）
**修复后**: 批量 IN 查询（3 查询）

- ✅ 批量查询 User nickname

---

## 6. PERF-REFORM-02: Redis 缓存层

### 评级: ✅ 通过

### 缓存工具 (`backend/app/utils/cache.py`)

- ✅ 所有缓存操作都包裹在 try/except 中，Redis 不可用时优雅降级
- ✅ `get_cached` 返回 None（缓存穿透时回源 DB）
- ✅ `set_cached` 返回 False（设置失败不影响业务）
- ✅ `delete_cached_pattern` 使用 SCAN（非 KEYS）避免阻塞 Redis
- ✅ Pydantic model 和 dict 的序列化/反序列化工具

### TTL 设置

| 缓存键 | TTL | 评价 |
|--------|-----|------|
| shop detail | 5 min | ✅ 合理 |
| product detail | 5 min | ✅ 合理 |
| config | 30 min | ✅ 合理（配置变更频率低） |
| shop list | 2 min | ✅ 合理 |
| admin stats | 1 min | ✅ 合理 |

### 缓存失效策略 — ⚠️ 不完整

当前只在读取时设置缓存，但**写操作（create/update/delete）后未主动清除相关缓存**。

**遗漏的缓存失效场景**:
1. 商家更新店铺信息后，`shop:detail:{id}` 缓存未失效
2. 商品上下架后，`product:detail:{id}` 和 `shop:detail:{id}` 缓存未失效
3. 管理员审核店铺后，`shop:list` 和 `admin:stats` 缓存未失效
4. 新用户注册后，`admin:stats` 缓存未失效

**影响**: 中。用户可能看到过期数据（最多 5 分钟），但不会导致数据不一致。对于 MVP 阶段可接受，但后续必须补充主动失效。

### 缓存穿透风险 — ✅ 低

- 当前设计：缓存 miss → 查 DB → 设置缓存。如果 DB 也查不到（如不存在的商品），不会设置缓存，可能导致穿透。
- 但商品、店铺等都有连续的整数 ID，攻击者难以枚举所有不存在的 ID，风险较低。

---

## 7. PERF-REFORM-03: 前端路由懒加载

### 评级: ✅ 通过

### React.lazy 配置 (`frontend/src/App.tsx`)

- ✅ 所有页面组件均使用 `React.lazy(() => import(...))` 懒加载
- ✅ Layout 组件（UserLayout, ShopLayout, RiderLayout, AdminLayout）保持静态导入（首次渲染需要）
- ✅ Login 和 Register 保持静态导入（入口页面）
- ✅ 统一的 Suspense fallback（全屏 Spin + "加载中..."提示）
- ✅ 无循环依赖风险（每个页面独立 chunk）
- ✅ 路由守卫（AuthGuard）正确保护各角色路由

---

## 8. UX-REFORM-02: 管理员订单管理增强

### 评级: ⚠️ 需改进

### 搜索功能 (`frontend/src/pages/admin/Orders.tsx`)

- ✅ Input.Search 组件，支持订单号/商家名搜索
- ✅ 搜索触发后重置页码
- ✅ 清除搜索时重置

### 后端搜索 (`backend/app/api/v1/admin.py:301-311`)

```python
if keyword:
    stmt = stmt.join(Shop, Order.shop_id == Shop.id, isouter=True)
    stmt = stmt.where(
        (Order.order_no.contains(keyword)) | (Shop.name.contains(keyword))
    )
```

- ✅ 使用 SQLAlchemy `contains()` 而非字符串拼接，自动参数化，**防止 SQL 注入**
- ✅ LEFT JOIN 确保无商家的订单也能显示

### 导出功能

- ✅ 前端 CSV 导出，BOM 头确保中文兼容
- ✅ 只导出当前页数据（简化实现）

### ⚠️ 手机号脱敏不一致

**问题**: `admin.py` 的 `list_all_orders`（Line 345）使用 `mask_phone()` 脱敏手机号，但 `get_admin_order_detail`（Line 383-384）返回**原始手机号**：

```python
# admin.py Line 383-384 (订单详情)
if user:
    order_data.user_phone = user.phone        # ← 原始手机号！
    order_data.user_nickname = user.nickname
```

而列表接口返回脱敏后的手机号：
```python
# admin.py Line 345 (订单列表)
order_data.user_phone = mask_phone(user.phone)  # ← 已脱敏
```

**风险**: 管理员订单详情接口暴露了用户完整手机号。虽然管理员有权限查看，但应与列表接口保持一致，或在设计上有意允许详情查看完整号码。需确认产品意图。

### 前端 AdminOrders.tsx 的 maskPhone 函数

- ✅ 前端也有 `maskPhone()` 函数用于二次脱敏（Line 23-26），在 Modal 详情中也调用了（Line 250, 258）

---

## 9. UX-REFORM-01: 图片上传验收

### 评级: ✅ 通过

### Review.tsx (`frontend/src/pages/user/Review.tsx`)

- ✅ 使用 `uploadApi.upload(file)` 上传图片
- ✅ 前端验证：`file.type.startsWith('image/')` 类型检查
- ✅ 前端验证：`file.size < 5MB` 大小限制
- ✅ 最多 3 张图片限制（`uploadedImages.length < 3`）
- ✅ 图片预览和删除功能
- ✅ 上传成功后将 URL 存入 `uploadedImages` 数组，提交时一起发送

### Products.tsx (`frontend/src/pages/shop/Products.tsx`)

- ✅ 使用 `uploadApi.upload(file)` 上传商品图片
- ✅ 同样的类型和大小验证
- ✅ 上传后自动填入表单 `image` 字段
- ✅ 图片预览功能

---

## 10. TEST-REFORM-01: 并发+边界测试

### 评级: ⚠️ 需改进

### 并发测试 (`backend/tests/test_phase2_concurrency.py`)

- ✅ `test_stock_safety_with_limited_stock`: 验证库存不会变负
- ✅ `test_duplicate_payment_idempotency`: 验证重复支付幂等性
- ✅ `test_concurrent_withdraw_balance_consistency`: 验证提现权限
- ✅ `test_cancel_order_restores_stock`: 验证取消订单恢复库存

**问题**:
1. ⚠️ 并发测试实际为串行执行（Line 131-147 使用 for 循环），注释中也承认 SQLite 不支持真正并发。这意味着**并发安全性未被真正验证**。
2. ⚠️ `test_cancel_order_restores_stock` 使用 PUT 请求支付（Line 306），但实际 API 是 POST（`orders.py:91`），可能导致测试失败。

### 边界测试 (`backend/tests/test_phase2_boundary.py`)

- ✅ 金额边界：0 元充值、负数充值、超限充值
- ✅ 库存边界：0 库存商品下单
- ✅ 分页边界：page=0、page=-1、page_size=1000
- ✅ 密码强度边界：无小写、无大写、无数字、长度不足

**覆盖面**: 合理，覆盖了主要边界情况。

---

## Phase 1 遗留问题跟踪

| 问题 | Phase 1 状态 | Phase 2 状态 |
|------|-------------|-------------|
| shop.py reject_order 缺少行锁 | ❌ 必须返工 | ❌ **仍未修复** |
| Schema 层金额字段用 float | ⚠️ 需改进 | ✅ **shop.py 已修复**（DecimalField） |
| coupons.py CouponResponse 用 float | ⚠️ 需改进 | ❌ **仍未修复** |
| 优惠券 remain_count 无行锁 | ⚠️ 需改进 | ❌ **仍未修复** |
| WebSocket close reason 信息泄露 | ⚠️ 需改进 | ✅ **已修复**（改为统一 "Unauthorized"） |
| 超时任务时区不一致 | ⚠️ 需改进 | ❌ 未确认 |
| CountdownTimer 双重触发 | ⚠️ 需改进 | ❌ 未确认 |
| Wallet.tsx 收款账号用 InputNumber | ⚠️ 需改进 | ❌ 未确认 |
| to_decimal() 重复定义 | ⚠️ 需改进 | ❌ 未确认 |

---

## 问题汇总

### ❌ 必须返工

| # | 文件 | 行号 | 问题 | 修复建议 |
|---|------|------|------|---------|
| 1 | `backend/app/services/audit.py` | 51 | 大额交易日志未脱敏金额 | 添加 `mask_amount(amount)` |
| 2 | `backend/app/api/v1/shop.py` | 553 | reject_order 还原库存缺少行锁（Phase 1 遗留） | 添加 `.with_for_update()` |

### ⚠️ 需改进

| # | 文件 | 行号 | 问题 | 修复建议 |
|---|------|------|------|---------|
| 3 | `backend/app/api/v1/coupons.py` | 22-23 | CouponResponse 金额字段仍用 float（Phase 1 遗留） | 改为 DecimalField |
| 4 | `backend/app/api/v1/coupons.py` | 99 | 优惠券 remain_count 扣减无行锁（Phase 1 遗留） | 添加 `with_for_update()` |
| 5 | `backend/app/api/v1/admin.py` | 383-384 | 订单详情返回原始手机号，与列表不一致 | 使用 `mask_phone()` 或确认产品意图 |
| 6 | `backend/app/utils/cache.py` | — | 写操作后未主动清除缓存 | 在关键写操作后调用 `delete_cached()` / `delete_cached_pattern()` |
| 7 | `backend/app/services/config.py` | 6-12 | MAX_LOGIN_ATTEMPTS/LOCK_DURATION_MINUTES 未在 DEFAULT_CONFIGS 中定义 | 添加到 DEFAULT_CONFIGS |
| 8 | `backend/tests/test_phase2_concurrency.py` | 306 | 支付 API 用 PUT 应为 POST | 改为 `client.post(...)` |

---

**最终判定: IS_PASS = NO**

存在 2 个必须返工问题（audit.py 金额未脱敏 + shop.py 行锁遗留），以及 Phase 1 的 coupons.py DecimalField 遗留问题未修复。建议修复所有 P0 问题后重新审查。
