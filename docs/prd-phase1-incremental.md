# FuYellowBlueRed Phase 1 增量 PRD

> 版本: v1.0 | 日期: 2026-05-19 | 基线文档: prd-final.md v4.0
> 来源: project-analysis-and-optimization.md v2.0 代码分析报告

---

## 文档说明

本文档为 Phase 1 紧急修复的增量需求定义，基于现有 PRD v4.0 基线，针对代码分析发现的 8 项紧急问题，补充详细需求规格。每项优化均包含需求ID、验收标准、影响范围和技术约束，供开发直接实施。

### 优先级定义

- **P0**: 必须完成，直接影响金融安全、核心功能可用性
- **P1**: 应当完成，影响接口规范、代码质量、用户体验

---

## SEC-REFORM-01: 金额字段 Float → Numeric(10,2)

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-01 |
| 优先级 | P0 |
| 类型 | 安全修复 |
| 预估工作量 | 2天 |
| 关联需求 | SEC-P0-06（账务事务完整）、F-P0-01~08（账务体系全链路） |

### 需求描述

将 `models.py` 中所有金额相关字段从 `Float` 类型迁移为 `Numeric(10, 2)`（即 DECIMAL），消除浮点精度丢失风险。金融场景下 Float 类型的精度问题可能导致资金计算误差，属于高危安全风险。

### 当前问题

`models.py` 中以下字段使用 `Float`，存在精度丢失：

| 模型 | 字段 | 当前类型 | 影响 |
|------|------|---------|------|
| Wallet | balance | Float | 余额精度 |
| Wallet | frozen_balance | Float | 冻结金额精度 |
| Order | total_amount | Float | 订单金额精度 |
| Order | discount_amount | Float | 优惠金额精度 |
| Order | delivery_fee | Float | 配送费精度 |
| OrderItem | price | Float | 商品单价精度 |
| Shop | min_order_amount | Float | 起送价精度 |
| Shop | delivery_fee | Float | 配送费精度 |
| Shop | rating | Float | 评分（可保留Float） |
| ShopEarning | goods_amount | Float | 商品金额精度 |
| ShopEarning | commission_rate | Float | 抽成比例精度 |
| ShopEarning | commission_amount | Float | 佣金金额精度 |
| ShopEarning | net_amount | Float | 净收入精度 |
| PlatformCommission | shop_commission | Float | 商家抽成精度 |
| PlatformCommission | rider_service_fee | Float | 骑手服务费精度 |
| PlatformCommission | total | Float | 总佣金精度 |
| FundFlow | amount | Float | 流水金额精度 |
| FundFlow | balance_before | Float | 变动前余额精度 |
| FundFlow | balance_after | Float | 变动后余额精度 |
| PaymentTransaction | amount | Float | 支付金额精度 |
| RiderEarning | amount | Float | 骑手收入精度 |
| WithdrawalRecord | amount | Float | 提现金额精度 |
| RefundRecord | refund_amount | Float | 退款金额精度 |
| Coupon | discount_amount | Float | 优惠金额精度 |
| Coupon | min_order_amount | Float | 最低订单金额精度 |
| FinanceAuditLog | amount | Float | 审计金额精度 |

> 注：`Shop.rating`、`UserAddress.latitude/longitude`、`Shop.latitude/longitude`、`Order.latitude/longitude` 为非金额字段，不在本次迁移范围内。

### 验收标准

1. 所有金额字段类型已从 `Float` 改为 `Numeric(10, 2)`，Python 侧类型注解改为 `Mapped[Decimal]`，默认值使用 `Decimal("0.00")`
2. 生成 Alembic 迁移脚本，迁移脚本可在 SQLite 和 MySQL 上正确执行
3. 已有数据迁移后精度无损（Float 存储的值转换为 Decimal 后数值一致）
4. 所有涉及金额计算的代码（FinanceService、OrderService、wallet 路由等）已适配 Decimal 类型，不再出现 float 隐式转换
5. 后端全部测试用例通过，金额比较使用 `Decimal` 而非 `==`

### 影响范围

- `backend/app/models/models.py` — 所有金额字段定义
- `backend/app/services/finance.py` — 资金计算逻辑
- `backend/app/services/order_service.py` — 订单金额计算
- `backend/app/api/v1/wallet.py` — 钱包接口
- `backend/app/api/v1/orders.py` — 订单接口
- `backend/app/schemas/` — 相关 Schema 的类型适配
- `backend/alembic/versions/` — 新增迁移脚本
- `backend/app/tasks/order_timeout.py` — 涉及金额的取消退款逻辑

### 技术约束

- 必须使用 `from sqlalchemy import Numeric` 和 `from decimal import Decimal`
- `Numeric(10, 2)` 表示最大 10 位数字、2 位小数，覆盖金额范围 -99999999.99 ~ 99999999.99
- 迁移脚本须兼容 SQLite（开发环境）和 MySQL（生产环境）
- 默认值从 `0.0` 改为 `Decimal("0.00")`，禁止 `float` 与 `Decimal` 混合运算
- Schema 层（Pydantic）的金额字段建议使用 `Decimal` 或 `str` 序列化，确保前端收到精确字符串而非浮点数
- 迁移需在测试环境验证数据无损后再合入主分支

---

## SEC-REFORM-02: 订单号生成改用雪花算法

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-02 |
| 优先级 | P0 |
| 类型 | 安全修复 |
| 预估工作量 | 0.5天 |
| 关联需求 | F-P0-02（唯一流水号）、SEC-P0-01（支付幂等） |

### 需求描述

将订单号生成逻辑从当前的时间戳+随机数方案改为雪花算法（Snowflake），消除高并发下的碰撞风险，同时保证订单号的趋势递增和全局唯一。

### 当前问题

```python
# orders.py L262, order_service.py L196
order_no = datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(100000, 999999)}"
```

- 秒级精度 + 6位随机数，同一秒内碰撞概率为 1/900000，高并发下风险显著
- 未做唯一性校验，碰撞后直接写入会导致数据库 `unique` 约束报错
- 可预测性强，存在订单枚举风险

### 验收标准

1. 订单号生成使用雪花算法，生成的 `order_no` 长度不超过 32 字符（数据库字段为 `String(32)`）
2. 相同毫秒内生成的订单号不重复，支持单机每毫秒 4096 个ID
3. 已移除所有旧的 `datetime.now().strftime(...) + random.randint(...)` 生成逻辑
4. `order_no` 字段已有 `unique` 约束，雪花算法生成后仍需保留该约束作为兜底
5. 现有订单号格式不受影响（历史数据保持不变）

### 影响范围

- `backend/app/api/v1/orders.py` — create_order 中的 order_no 生成
- `backend/app/services/order_service.py` — create_order 中的 order_no 生成
- `backend/app/utils/` — 新增 `snowflake.py` 雪花算法工具模块

### 技术约束

- 雪花算法实现需考虑时钟回拨问题：检测到回拨时抛出异常而非生成重复ID
- worker_id 和 datacenter_id 可从配置中读取，默认值为 1（单实例部署场景）
- 生成的ID为 64 位整数，转为字符串后作为 order_no 存储
- 交易流水号 `trade_no`（PaymentTransaction）如也使用类似逻辑，建议一并改造
- 算法需无第三方依赖，纯 Python 实现

---

## SEC-REFORM-03: WebSocket 添加 JWT 认证

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-03 |
| 优先级 | P0 |
| 类型 | 安全修复 |
| 预估工作量 | 1天 |
| 关联需求 | SEC-P0-04（JWT密钥安全）、SEC-P2-01（Token存储升级） |

### 需求描述

为 WebSocket 连接添加 JWT 认证，防止任何人冒充任意 user_id 连接 WebSocket 接收/发送消息。

### 当前问题

```python
# main.py L152-154
@app.websocket("/ws/{channel}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, channel: str, user_id: str):
    await websocket.accept()  # 无需认证即可连接
```

任何人可伪造 `user_id` 连接 WebSocket，接收该用户的通知消息，或向频道广播消息。

### 验收标准

1. WebSocket 连接时必须验证 JWT Token，未携带 Token 或 Token 无效时拒绝连接（关闭 WebSocket，返回 4001 状态码）
2. Token 验证通过后，从 Token payload 中提取 `user_id`，与 URL 中的 `user_id` 一致才允许连接，不一致则拒绝
3. 支持 Token 通过 query parameter 传递（如 `ws://host/ws/channel/userId?token=xxx`），兼容浏览器 WebSocket API
4. 已连接的 WebSocket 在 Token 过期后无需断开（长连接场景），但新连接必须使用有效 Token
5. 连接拒绝时记录安全日志

### 影响范围

- `backend/app/main.py` — websocket_endpoint 函数
- `backend/app/utils/auth.py` — 复用 verify_token 逻辑
- `frontend/src/` — WebSocket 连接代码需传递 Token（如有前端 WebSocket 客户端）

### 技术约束

- Token 传递方式：query parameter（`?token=xxx`），因为浏览器 WebSocket API 不支持自定义 Header
- 验证逻辑复用 `app.utils.auth.verify_token` 和 `is_token_valid`，不重复实现
- 拒绝连接使用 `websocket.close(code=4001, reason="Unauthorized")`，不使用 HTTP 401（WebSocket 握手后无法返回 HTTP 状态码）
- 不影响现有 HTTP 接口的认证逻辑

---

## API-REFORM-01: require_role 返回 403 而非 401

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | API-REFORM-01 |
| 优先级 | P1 |
| 类型 | 接口规范 |
| 预估工作量 | 0.5天 |
| 关联需求 | 全局权限体系 |

### 需求描述

将 `require_role` 装饰器中权限不足时的响应状态码从 401（未认证）改为 403（禁止访问），使 HTTP 语义正确：401 表示"未登录"，403 表示"已登录但权限不足"。

### 当前问题

```python
# deps/auth.py L57-62
def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise UnauthorizedException("权限不足")  # 401，应为 403
        return current_user
    return role_checker
```

`ForbiddenException` 已在 `exceptions.py` 中定义（返回 403），但未被使用。权限不足与未认证混淆，导致前端无法区分"需要登录"和"没有权限"两种场景。

### 验收标准

1. `require_role` 中权限不足时抛出 `ForbiddenException("权限不足")`（403），而非 `UnauthorizedException`
2. 前端根据 401/403 状态码区分处理：401 跳转登录页，403 显示"无权限"提示
3. 所有使用 `require_role` 的接口行为一致：未登录返回 401，已登录但角色不匹配返回 403
4. `get_current_user` 中的认证失败仍然返回 401（未登录场景不受影响）

### 影响范围

- `backend/app/deps/auth.py` — require_role 函数，1 行改动
- `frontend/src/services/api.ts` — HTTP 拦截器中 401/403 的区分处理
- `frontend/src/` — 相关页面的权限提示逻辑

### 技术约束

- `ForbiddenException` 已存在，直接替换即可
- 改动极小，但需要前端配合更新拦截器逻辑
- 注意：如果前端有硬编码判断 401 来处理"权限不足"的逻辑，需一并修改

---

## SEC-REFORM-04: 库存扣减加 SELECT FOR UPDATE 行锁

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-04 |
| 优先级 | P0 |
| 类型 | 并发安全 |
| 预估工作量 | 1天 |
| 关联需求 | F-P0-01（钱包支付）、U-P0-01（取消订单/退库存） |

### 需求描述

在创建订单扣减库存时，使用 `SELECT ... FOR UPDATE` 行锁锁定库存行，防止高并发下超卖。

### 当前问题

```python
# orders.py / order_service.py create_order
product = product_result.scalar_one_or_none()
# 未锁定行，并发请求可能同时读到 stock > 0
product.stock -= quantity  # 并发下可能超卖
```

多个并发请求同时读到库存充足，同时扣减，导致实际扣减后库存为负数。

### 验收标准

1. 创建订单扣减库存时，使用 `select(Product).where(Product.id == product_id).with_for_update()` 锁定行
2. 锁定后再次检查库存是否充足（`if product.stock < quantity: raise BadRequestException("库存不足")`），形成"先锁后检"模式
3. 取消订单回补库存时同样使用行锁，防止回补与扣减的并发冲突
4. 库存扣减/回补必须在数据库事务内执行，与订单创建/取消为同一事务
5. 并发测试：10 个并发请求抢购库存为 5 的商品，最终成功下单数 ≤ 5，库存不出现负数

### 影响范围

- `backend/app/api/v1/orders.py` — create_order、cancel_order 中的库存操作
- `backend/app/services/order_service.py` — create_order、cancel_order 中的库存操作

### 技术约束

- SQLite 不支持 `SELECT FOR UPDATE`（会静默忽略），因此此修复在生产环境（MySQL）才真正生效
- 开发环境（SQLite）可通过应用层逻辑兜底：扣减后检查 `product.stock >= 0`，若为负则回滚
- 锁的粒度为行级（单个 Product 行），不影响其他商品的并发下单
- 事务范围应尽量小，避免长时间持有行锁
- 注意与 SEC-REFORM-06（API统一调用Service层）的依赖关系：库存扣减逻辑最终应统一到 Service 层

---

## CODE-REFORM-01: API 路由统一调用 Service 层（删除重复代码）

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | CODE-REFORM-01 |
| 优先级 | P1 |
| 类型 | 代码质量 |
| 预估工作量 | 3天 |
| 关联需求 | 全局代码架构、所有订单相关需求 |

### 需求描述

将 `api/v1/orders.py` 中直接操作数据库的业务逻辑，统一迁移到 `services/order_service.py` 的 `OrderService` 类中，API 路由仅负责参数校验、调用 Service、返回响应。消除两处重复代码，遵守 DRY 原则。

### 当前问题

`orders.py` 和 `order_service.py` 中存在几乎完全重复的代码：

| 功能 | orders.py（路由） | order_service.py（服务层） | 问题 |
|------|-------------------|--------------------------|------|
| get_cart | 直接查DB | 同样逻辑 | 重复 |
| add_to_cart | 直接查DB | 同样逻辑 | 重复 |
| update_cart_item | 直接查DB | 同样逻辑 | 重复 |
| remove_cart_item | 直接查DB | 同样逻辑 | 重复 |
| create_order | 直接查DB | 同样逻辑 | 重复 |
| cancel_order | 直接查DB | 同样逻辑 | 重复 |

API 路由直接操作数据库绕过了 Service 层，修改业务逻辑需要同步两处，极易遗漏。

### 验收标准

1. `api/v1/orders.py` 中所有直接数据库操作已移除，改为调用 `OrderService` 的对应方法
2. `OrderService` 的方法签名完整，包含所有必要的参数（user_id、request body 等）
3. API 路由函数仅保留：参数提取 → 调用 Service → 返回 Response 的三层结构
4. `OrderService` 已处理所有业务逻辑校验（库存检查、状态流转、金额计算等）
5. 所有后端测试用例通过，功能行为与重构前一致

### 影响范围

- `backend/app/api/v1/orders.py` — 主要重构文件，删除所有 DB 操作
- `backend/app/services/order_service.py` — 补充完善 Service 方法
- `backend/app/tasks/order_timeout.py` — 已使用 OrderService，无需改动

### 技术约束

- 重构为纯代码搬迁，不改变任何业务逻辑和接口行为
- Service 方法需接收 `db: AsyncSession` 参数（通过构造函数），路由通过 `Depends(get_db)` 注入后传入
- Service 方法的返回值应与路由需要的格式一致，路由层只做 Schema 转换
- 建议在重构时一并修复 orders.py 中的 N+1 查询问题（Phase 2 内容，但如改动同一代码段可提前处理）
- 此项是 SEC-REFORM-04（库存行锁）的前置依赖：库存扣减逻辑统一到 Service 层后，行锁加在 Service 层

---

## U-P0-02: 支付倒计时 + 订单超时自动取消

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | U-P0-02 |
| 优先级 | P0 |
| 类型 | 功能缺失 |
| 预估工作量 | 3天 |
| 关联需求 | U-P0-01（用户取消订单）、F-P0-06（退款回滚）、SEC-REFORM-04（库存行锁） |

### 需求描述

实现完整的支付倒计时与订单超时自动取消功能，覆盖前端倒计时展示与后端超时调度两个维度。用户下单后 15 分钟内未支付，系统自动取消订单、回补库存、退款（如有预扣）、状态归档。

### 当前实现状态

经代码核查，该功能**已有基础实现但存在缺陷**：

| 维度 | 已实现 | 缺失/缺陷 |
|------|--------|----------|
| 前端倒计时组件 | CountdownTimer 组件已存在 | 仅在支付弹窗中展示，订单列表中未展示倒计时 |
| 支付弹窗倒计时 | Orders.tsx 中支付弹窗有倒计时 | 倒计时归零后仅前端提示，未主动调用后端取消 |
| 后端超时任务 | OrderTimeoutTask 每60s扫描 | 无分布式锁，多实例会重复执行；无取消后库存回补确认 |
| 订单列表倒计时 | — | 订单卡片上无倒计时显示，用户无法直观感知剩余支付时间 |
| 超时后状态同步 | — | 前端轮询间隔5秒，存在延迟；超时取消后无主动推送通知 |

### 用户故事

1. 作为消费者，我下单后能在订单列表中看到每个待支付订单的剩余支付时间，以便及时完成支付
2. 作为消费者，支付倒计时最后5分钟变为红色警告，提醒我尽快支付
3. 作为消费者，超时后订单自动变为"已取消"状态，我不需要手动操作
4. 作为商家，超时取消的订单自动回补库存，我无需手动处理
5. 作为系统，多实例部署时超时任务不重复执行，避免重复取消

### 业务流程

```
用户下单 → 订单创建（状态: PENDING_PAYMENT）
              ↓
      ┌─ 前端展示15分钟倒计时 ─┐
      │   (订单列表 + 支付弹窗)  │
      └────────────────────────┘
              ↓
    ┌───── 15分钟内 ─────┐
    │                    │
  用户支付            用户不操作
    │                    │
    ↓                    ↓
 订单状态变更      倒计时归零（前端提示）
 PENDING_ACCEPT         │
                        ↓
              后端定时任务扫描（每60s）
                        │
              ┌─────────┴─────────┐
              │ 超时订单存在？      │
              └─────────┬─────────┘
                   是   │   否 → 结束
                        ↓
              ┌─ 逐个处理超时订单 ─┐
              │ 1. 状态→CANCELLED  │
              │ 2. 回补库存(+行锁) │
              │ 3. 如已支付→退款   │
              │ 4. 记录取消原因     │
              │ 5. 清空相关购物车   │
              └───────────────────┘
                        ↓
              前端下次轮询时更新状态
```

### 异常流程

| 异常场景 | 处理方式 |
|---------|---------|
| 倒计时即将归零时用户正在支付 | 支付请求到达后端时先检查订单状态，若已超时取消则返回"订单已超时取消"，前端展示相应提示 |
| 前端与服务器时间偏差大 | 倒计时以后端返回的 `created_at` 为准，前端不依赖本地时间 |
| 多实例同时扫描到同一超时订单 | 使用 Redis 分布式锁（`order_timeout:{order_id}`），确保只有一个实例处理 |
| 超时取消时库存回补失败 | 整个取消操作在同一事务中，回补失败则整体回滚，下次调度重试 |
| 用户在倒计时最后几秒内取消订单 | 正常取消流程，不触发超时取消（订单状态已变为 CANCELLED） |
| 已支付订单不应被超时取消 | 超时扫描仅针对 `PENDING_PAYMENT` 状态的订单 |

### 页面交互设计

**1. 订单列表 — 待支付订单卡片**

```
┌──────────────────────────────────────────┐
│ 🏪 黄焖鸡米饭          [待支付]          │
│ 订单号：20260519143000001                 │
│ 黄焖鸡×1、米饭×1                          │
│ ¥28.00                                   │
│ ⏱ 剩余支付时间: 12:34                     │  ← 新增：倒计时显示
│                                          │
│ [查看详情]  [取消订单]  [立即支付]          │
└──────────────────────────────────────────┘
```

- 倒计时文字颜色：剩余 > 5分钟 为蓝色（#1890ff），≤ 5分钟 为红色（#ff4d4f）
- 倒计时归零后：订单卡片状态自动切换为"已取消"，倒计时文字替换为"已超时取消"

**2. 支付弹窗（已有，需优化）**

```
┌──────────────────────────────────────┐
│          订单支付                     │
│                                      │
│   剩余支付时间                        │
│       ⏱ 12:34                        │  ← 已有，保持
│                                      │
│   订单号：20260519143000001           │
│   支付金额：¥28.00                    │
│                                      │
│   [  立即支付  ]                      │
│   [  取消订单  ]                      │
└──────────────────────────────────────┘
```

- 倒计时归零后自动关闭弹窗，显示"订单支付超时，已自动取消"提示
- 优化：倒计时归零时主动调用 `cancelOrder` API（标记原因"支付超时"），而非仅等后端定时任务

**3. 订单详情弹窗 — 超时取消订单**

```
┌──────────────────────────────────────┐
│  订单号：20260519143000001            │
│  商家：黄焖鸡米饭                     │
│  订单金额：¥28.00                     │
│                                      │
│  订单状态：                           │
│  ● 订单创建 — 2026-05-19 14:30:00    │
│  ● 已取消 — 支付超时自动取消          │  ← 超时取消原因
└──────────────────────────────────────┘
```

### 验收标准

1. 订单列表中，`PENDING_PAYMENT` 状态的订单卡片显示 15 分钟倒计时，倒计时基于后端 `created_at` 计算
2. 倒计时最后 5 分钟文字变为红色警告
3. 支付弹窗倒计时归零时，前端主动调用取消接口，弹出"订单支付超时，已自动取消"提示
4. 后端 `OrderTimeoutTask` 每 60 秒扫描并取消超时订单，取消时回补库存、记录取消原因
5. 超时取消使用 Redis 分布式锁，防止多实例重复执行
6. 已支付（非 PENDING_PAYMENT 状态）的订单不会被超时任务取消

### 影响范围

- `frontend/src/pages/user/Orders.tsx` — 订单列表增加倒计时显示
- `frontend/src/components/CountdownTimer/index.tsx` — 组件复用，可能需调整样式
- `backend/app/tasks/order_timeout.py` — 增加分布式锁、库存回补确认
- `backend/app/services/order_service.py` — cancel_order 方法需支持超时取消类型
- `backend/app/utils/redis_client.py` — 分布式锁工具方法

### 技术约束

- 前端倒计时以后端 `created_at` 为基准，计算 `created_at + 15min - now`，不依赖本地时间
- 后端超时任务的分布式锁使用 Redis SETNX 实现，锁超时时间 30 秒，确保不死锁
- 取消原因统一记录为"支付超时自动取消"，cancel_type 为 "timeout"
- 超时取消与用户手动取消走同一 `cancel_order` 方法，通过 `cancel_type` 参数区分

---

## U-P2-03-FE: 用户钱包前端页面

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | U-P2-03-FE |
| 优先级 | P1 |
| 类型 | 功能缺失（前端） |
| 预估工作量 | 2天 |
| 关联需求 | U-P2-03（用户钱包）、F-P0-01（余额支付）、F-P0-05（资金流水） |

### 需求描述

完善用户钱包前端页面，实现余额展示、交易记录分页、充值申请入口等功能，使后端已有的钱包 API 能力在前端完整呈现。

### 当前实现状态

经代码核查，钱包页面**已有基础实现**但功能不完整：

| 维度 | 已实现 | 缺失/缺陷 |
|------|--------|----------|
| 页面路由 | `/user/wallet` 已注册，UserLayout 中菜单已有入口 | — |
| 余额展示 | 展示余额、冻结金额、渐变背景卡片 | — |
| 交易记录 | 展示类型标签、金额、时间 | 无分页控件（仅加载第一页），无下拉刷新 |
| 充值功能 | 说明文字"联系客服充值" | 无充值申请入口/流程 |
| 交易类型映射 | 7种类型映射已实现 | — |
| 空状态 | Empty 组件已使用 | — |
| 移动端适配 | isMobile 响应式已实现 | — |

### 用户故事

1. 作为消费者，我在钱包页面能看到当前余额和冻结金额，了解可用资金
2. 作为消费者，我能查看所有交易记录并翻页加载历史记录，追溯资金变动
3. 作为消费者，我想充值时能在钱包页面发起充值申请（非自主充值，需管理员审批）
4. 作为商家/骑手，我能在钱包页面申请提现（满足最低提现金额时）
5. 作为消费者，交易记录中收入和支出有明显的视觉区分

### 业务流程

**充值申请流程：**

```
用户点击"充值" → 弹出充值申请弹窗
    ↓
输入充值金额 → 确认提交
    ↓
后端创建充值申请记录（状态: PENDING）
    ↓
管理员在后台审批 → 通过后余额增加
    ↓
用户在交易记录中看到充值到账
```

**提现申请流程（商家/骑手）：**

```
用户点击"提现" → 弹出提现申请弹窗
    ↓
输入提现金额 + 选择提现方式 → 确认提交
    ↓
后端校验余额充足 + 最低提现金额 → 创建提现记录
    ↓
管理员审批 → 通过后余额减少
    ↓
用户在交易记录中看到提现扣款
```

### 异常流程

| 异常场景 | 处理方式 |
|---------|---------|
| 充值金额为 0 或负数 | 前端表单校验拦截，提示"请输入有效金额" |
| 充值金额超过单笔限额 | 前端提示限额，后端二次校验返回错误 |
| 提现金额 > 可用余额 | 提示"余额不足" |
| 提现金额 < 最低提现金额 | 提示最低提现金额（从后端配置获取） |
| 交易记录加载失败 | 显示错误提示 + 重试按钮 |
| 余额与交易记录不一致 | 展示以后端余额为准，交易记录分页加载 |

### 页面交互设计

**1. 钱包主页（增强版）**

```
┌──────────────────────────────────────────┐
│ 我的钱包                          [?说明] │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓       │
│       账户余额（元）                       │
│          ¥ 128.50                         │
│       冻结金额：¥ 0.00                    │
│                                          │
│   [ 充值 ]          [ 提现 ]              │  ← 新增：操作按钮
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ 📋 交易记录                               │
│                                          │
│ [支付] -¥28.00        2026-05-19 14:30   │
│ [充值] +¥100.00       2026-05-18 10:00   │
│ [退款] +¥15.00        2026-05-17 12:00   │
│ ...                                      │
│                                          │
│        ← 1  2  3  4  5 →                 │  ← 新增：分页控件
└──────────────────────────────────────────┘
```

**2. 充值弹窗**

```
┌──────────────────────────────────────┐
│  充值申请                             │
│                                      │
│  充值金额：[ ___________ ] 元         │
│                                      │
│  快捷金额：                           │
│  [ ¥50 ]  [ ¥100 ]  [ ¥200 ]  [ ¥500 ]│
│                                      │
│  ⚠ 充值需管理员审核后到账              │
│                                      │
│  [  取消  ]    [  提交申请  ]          │
└──────────────────────────────────────┘
```

**3. 提现弹窗（商家/骑手角色显示）**

```
┌──────────────────────────────────────┐
│  申请提现                             │
│                                      │
│  可提现余额：¥128.50                  │
│  最低提现金额：¥10.00                  │
│                                      │
│  提现金额：[ ___________ ] 元         │
│  提现方式：[ 支付宝 ▼ ]               │
│  收款账号：[ ___________ ]             │
│                                      │
│  [  取消  ]    [  提交申请  ]          │
└──────────────────────────────────────┘
```

**4. 交易记录增强**

- 收入类（充值、退款、收入）：绿色文字，`+` 前缀
- 支出类（支付、提现、佣金、服务费）：红色文字，`-` 前缀
- 分页：每页 20 条，底部分页器
- 支持按类型筛选（可选）：全部 / 收入 / 支出

### 验收标准

1. 钱包页面正确展示余额和冻结金额，数据与后端 `/wallet` 接口一致
2. 交易记录支持分页加载，底部分页器可翻页，每页 20 条
3. 充值按钮打开充值弹窗，支持输入金额和快捷金额选择，提交后调用后端接口
4. 提现按钮仅对 SHOP_OWNER 和 RIDER 角色显示，提交前校验余额和最低提现金额
5. 交易记录中收入和支出有明显的颜色区分（绿色/红色）
6. 移动端和桌面端均正常展示和交互

### 影响范围

- `frontend/src/pages/user/Wallet.tsx` — 主要重构文件
- `frontend/src/services/wallet.ts` — 可能需补充充值/提现 API 方法
- `frontend/src/layouts/UserLayout.tsx` — 菜单入口已存在，无需改动
- `backend/app/api/v1/wallet.py` — 确认充值申请接口是否存在，如无则需新增
- `backend/app/api/v1/rider.py` — 提现接口已存在

### 技术约束

- 充值功能当前仅管理员可操作（SEC-P0-05），前端充值按钮为"申请"性质，需新增后端充值申请接口或在现有接口基础上增加审批流程
- 如不新增审批流程，充值按钮可改为"联系客服充值"的交互（展示客服联系方式），与当前逻辑一致但 UI 更友好
- 提现接口 `POST /rider/withdraw` 已存在，前端直接调用
- 分页使用 Ant Design 的 `Pagination` 组件
- 金额展示统一使用 `toFixed(2)` 保留两位小数
- 所有金额输入框使用 `InputNumber` 组件，限制小数位数为 2 位

---

## 依赖关系与实施顺序

```
SEC-REFORM-01 (Float→Numeric)     ─┐
SEC-REFORM-02 (雪花算法)           ─┤  可并行
SEC-REFORM-03 (WebSocket认证)      ─┤
API-REFORM-01 (403改403)          ─┤
SEC-REFORM-04 (库存行锁)           ─┘
         ↓
CODE-REFORM-01 (API→Service重构)   ← 依赖 SEC-REFORM-04 的行锁逻辑最终放在 Service 层
         ↓
U-P0-02 (支付倒计时+超时取消)       ← 依赖 CODE-REFORM-01（cancel_order 统一在 Service 层）
         ↓
U-P2-03-FE (钱包前端页面)           ← 独立，可与其他项并行
```

### 建议分组实施

| 批次 | 内容 | 预估工期 |
|------|------|---------|
| 第1批（并行） | SEC-REFORM-01 + SEC-REFORM-02 + SEC-REFORM-03 + API-REFORM-01 | 2天 |
| 第2批 | SEC-REFORM-04 + CODE-REFORM-01 | 4天 |
| 第3批（并行） | U-P0-02 + U-P2-03-FE | 3天 |
| **合计** | | **~9个工作日** |

---

## 文件变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-05-19 | 初始版本，定义 Phase 1 全部 8 项增量需求 |
