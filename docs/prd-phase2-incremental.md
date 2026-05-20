# FuYellowBlueRed Phase 2 增量 PRD

> 版本: v1.0 | 日期: 2026-05-19 | 基线文档: prd-final.md v4.0
> 前置依赖: Phase 1 已全部完成（250 测试通过）
> 来源: project-analysis-and-optimization.md v2.0 代码分析报告

---

## 文档说明

本文档为 Phase 2 质量提升的增量需求定义，基于现有 PRD v4.0 基线和 Phase 1 完成后的代码现状。每项优化均包含需求ID、验收标准、影响范围和技术约束。

### 优先级定义

- **P0**: 必须完成，直接影响系统安全、数据可靠性
- **P1**: 应当完成，显著提升性能、安全防御、用户体验

### Phase 1 已完成项回顾

以下 Phase 1 优化已完成并合入代码，Phase 2 部分需求与之存在依赖：

| 需求ID | 描述 | 完成状态 |
|--------|------|---------|
| SEC-REFORM-01 | 金额字段 Float → Numeric(10,2) | ✅ 已完成 |
| SEC-REFORM-02 | 订单号改用雪花算法 | ✅ 已完成 |
| SEC-REFORM-03 | WebSocket JWT 认证 | ✅ 已完成 |
| API-REFORM-01 | require_role 返回 403 | ✅ 已完成 |
| SEC-REFORM-04 | 库存扣减加 SELECT FOR UPDATE | ✅ 已完成 |
| CODE-REFORM-01 | API 路由统一调用 Service 层 | ✅ 已完成 |
| U-P0-02 | 支付倒计时 + 订单超时自动取消 | ✅ 已完成 |
| U-P2-03-FE | 用户钱包前端页面 | ✅ 已完成 |

---

## PERF-REFORM-01: 修复所有 N+1 查询

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | PERF-REFORM-01 |
| 优先级 | P1 |
| 类型 | 性能优化 |
| 预估工作量 | 3天 |
| 关联需求 | PERF-REFORM-02（缓存层）、非功能需求 8.1（接口响应≤300ms） |
| Phase 1 依赖 | CODE-REFORM-01（Service 层统一后，N+1 修复集中在 Service 层） |

### 需求描述

识别并修复后端所有 N+1 查询问题，使用 `selectinload`/`joinedload` 预加载关联数据，或将循环内逐条查询改为批量 IN 查询，显著减少数据库访问次数。

### 当前问题清单（代码核查）

| 位置 | 方法 | N+1 模式 | 影响 |
|------|------|---------|------|
| `order_service.py:53-76` | `get_cart` | 对每个 CartItem 逐个查询 Product 和 Shop | 购物车 N 项 → 2N+1 次查询 |
| `order_service.py:356-368` | `get_orders` | 对每个 Order 逐个查询 Shop 和 OrderItem | 列表 N 单 → 2N+1 次查询 |
| `order_service.py:370-392` | `get_order_detail` | 单独查询 Shop 和 OrderItem | 3 次查询可合并为 1 次 |
| `order_service.py:463-486` | `cancel_order` | 逐个查询 Product 回补库存 | N 项 → N 次查询 |
| `admin.py:295-301` | `list_all_orders` | 对每个 Order 逐个查询 Shop | 管理列表 N 单 → N+1 次查询 |
| `admin.py:330-341` | `get_admin_order_detail` | 单独查询 Shop 和 User | 3 次查询可合并 |
| `review.py:95-103` | `get_shop_reviews` | 对每个 Review 逐个查询 User | 评价列表 N 条 → N+1 次查询 |
| `shop.py` (商家订单) | 商家订单列表 | 类似 N+1 模式 | 待确认 |

### 验收标准

1. `get_cart` 使用 `selectinload(CartItem.product, CartItem.shop)` 预加载，查询次数从 2N+1 降为 2~3 次
2. `get_orders` / `get_order_detail` 使用 `selectinload(Order.items)` + `joinedload(Order.shop)` 预加载，消除循环内查询
3. `list_all_orders`（管理端）和 `get_shop_reviews` 同样使用预加载消除 N+1
4. `cancel_order` 中库存回补使用批量 `IN` 查询（`Product.id.in_(product_ids)`），替代逐个查询
5. 所有修改后的接口响应时间 P95 不超过 300ms（非功能需求 8.1）

### 影响范围

- `backend/app/services/order_service.py` — 主要修复文件
- `backend/app/api/v1/admin.py` — 管理端订单查询
- `backend/app/api/v1/review.py` — 评价列表查询
- `backend/app/api/v1/shop.py` — 商家端订单查询（如有 N+1）
- `backend/app/models/models.py` — 可能需要补充 relationship 的 lazy 策略

### 技术约束

- 优先使用 `selectinload`（独立查询，不改变主查询结构）而非 `joinedload`（可能产生笛卡尔积）
- 对于列表页场景（orders、reviews），`selectinload` 配合批量 IN 查询是最佳方案
- 预加载仅用于实际需要关联数据的接口，不影响不需要关联数据的查询
- 修改后需确保 Pydantic Schema 的 `model_validate` 仍能正确序列化预加载的数据
- `with_for_update()` 与 `selectinload` 不应同时使用（行锁场景保持现有逐个查询模式）

---

## PERF-REFORM-02: 添加 Redis 缓存层

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | PERF-REFORM-02 |
| 优先级 | P1 |
| 类型 | 性能优化 |
| 预估工作量 | 2天 |
| 关联需求 | 非功能需求 8.1（接口响应≤300ms） |
| Phase 1 依赖 | SEC-REFORM-03（Redis 已在 Phase 1 中用于 Token 黑名单和分布式锁） |

### 需求描述

利用已有的 Redis 客户端（`redis_client.py` 已提供 `get_cache`/`set_cache`/`delete_cache`），为热点数据添加缓存层，减少数据库查询压力。

### 缓存目标清单

| 数据 | 缓存Key | TTL | 失效触发 |
|------|---------|-----|---------|
| 商家详情 | `cache:shop:{id}` | 5min | 商家信息更新时主动失效 |
| 商品详情 | `cache:product:{id}` | 5min | 商品创建/更新/删除时失效 |
| 平台配置 | `cache:config:{key}` | 30min | 配置更新时主动失效 |
| 商家列表（首页） | `cache:shops:page:{page}:{status}` | 2min | 新商家审核通过时失效 |
| 管理端统计数据 | `cache:admin:stats` | 1min | 无需主动失效（自然过期） |

### 验收标准

1. 商家详情和商品详情查询优先从 Redis 读取，缓存未命中时查询数据库并写入缓存
2. 商家信息/商品信息更新时，主动删除对应缓存 Key
3. 平台配置查询优先走缓存，配置更新时主动失效
4. Redis 不可用时不影响业务（降级为直接查询数据库），不抛出异常
5. 缓存命中时接口响应时间降至 50ms 以内

### 影响范围

- `backend/app/api/v1/shop.py` — 商家/商品查询添加缓存逻辑
- `backend/app/api/v1/config.py` — 配置查询添加缓存逻辑
- `backend/app/api/v1/admin.py` — 管理统计添加缓存逻辑
- `backend/app/utils/redis_client.py` — 已有基础方法，可能需扩展批量删除

### 技术约束

- 复用现有 `redis_client.get_cache`/`set_cache`/`delete_cache` 方法，不新增 Redis 客户端
- Redis 不可用时静默降级（`is_connected` 检查已有），不中断业务
- 缓存序列化使用 JSON，反序列化后需要重建 Pydantic Schema 对象
- 缓存 Key 命名统一前缀 `cache:`，与现有 Token 黑名单 `token:` 前缀区分
- 写操作（创建/更新/删除）不缓存，仅缓存读操作
- 列表缓存 Key 需包含分页参数，避免不同页的数据混淆

---

## PERF-REFORM-03: 前端路由懒加载

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | PERF-REFORM-03 |
| 优先级 | P1 |
| 类型 | 性能优化 |
| 预估工作量 | 1天 |
| 关联需求 | 非功能需求 8.1（首屏加载≤3s） |

### 需求描述

将 `App.tsx` 中所有页面组件的静态导入改为 `React.lazy` 动态导入，实现代码分割，减少首屏加载体积。

### 当前问题

`App.tsx` 中 30+ 个页面组件全部使用 `import` 静态导入，打包后首屏 JS 包体积大，加载慢。

### 验收标准

1. 所有页面组件改为 `React.lazy(() => import(...))` 动态导入
2. 使用 `<Suspense fallback={<Loading />}>` 包裹路由出口，加载中显示统一的 Loading 组件
3. Vite 构建后生成多个 chunk 文件，首屏仅加载核心 chunk + 首页 chunk
4. 首屏加载时间从 ~3s 降至 ~1.5s
5. 路由切换正常，无白屏闪烁

### 影响范围

- `frontend/src/App.tsx` — 主要修改文件，所有 import 改为 lazy
- `frontend/src/components/Loading.tsx` — 作为 Suspense fallback

### 技术约束

- 使用 `React.lazy` + `Suspense`，不引入额外依赖
- 每个页面组件一个 chunk，Vite 自动根据 import 路径分 chunk
- Layout 组件（UserLayout、ShopLayout 等）保持静态导入（它们是框架组件，首屏必须）
- ErrorBoundary 组件已有，无需新增
- 注意：懒加载后组件类型会变为 `LazyExoticComponent`，确保 `AuthGuard` 等包装组件兼容

---

## TEST-REFORM-01: 添加并发测试 + 边界测试

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | TEST-REFORM-01 |
| 优先级 | P1 |
| 类型 | 测试质量 |
| 预估工作量 | 3天 |
| 关联需求 | SEC-REFORM-04（库存行锁需并发测试验证）、F-P0-01（钱包支付需并发测试） |
| Phase 1 依赖 | SEC-REFORM-04（行锁已加，需测试验证有效性） |

### 需求描述

为金融操作和库存操作添加并发测试，为金额和数量字段添加边界值测试，弥补当前测试覆盖的空白。

### 测试场景清单

**并发测试（4 项）：**

| 测试场景 | 测试目标 | 预期结果 |
|---------|---------|---------|
| 10 并发抢购库存为 5 的商品 | 库存行锁有效性 | 成功下单数 ≤ 5，库存不出现负数 |
| 同一订单并发支付 | 支付幂等性 | 仅一次支付成功，余额只扣一次 |
| 并发创建订单 + 并发取消订单 | 事务一致性 | 库存最终一致，不超卖不多卖 |
| 同一钱包并发提现 | 余额一致性 | 余额不出现负数，提现总额不超过余额 |

**边界值测试（4 项）：**

| 测试场景 | 边界值 | 预期结果 |
|---------|--------|---------|
| 金额边界 | 0 元订单、负数金额、超大金额（99999999.99） | 正确拒绝或处理 |
| 库存边界 | 0 库存商品下单、负库存检查 | 正确拒绝"库存不足" |
| 分页边界 | page=0、page=-1、page_size=0、page_size=1000 | 参数校验生效 |
| 充值限额边界 | 单笔 10000.01 元、单日累计超 50000 | 限额检查生效 |

### 验收标准

1. 并发测试使用 `asyncio.gather` 或 `pytest-asyncio` 的并发机制，模拟真实并发场景
2. 4 项并发测试全部通过，验证行锁和幂等机制有效
3. 4 项边界值测试全部通过，覆盖 0 值、负值、超大值场景
4. 测试文件放置在 `backend/tests/` 目录，命名规范：`test_concurrency.py`、`test_boundary.py`
5. 现有测试不受影响，全部通过

### 影响范围

- `backend/tests/test_concurrency.py` — 新增文件
- `backend/tests/test_boundary.py` — 新增文件
- `backend/tests/conftest.py` — 可能需要扩展测试 fixtures

### 技术约束

- 并发测试使用 `asyncio.gather` 发起并发请求，不引入多进程
- SQLite 不支持真正的并发写入，并发测试需标注 `@pytest.mark.skipif` 在 SQLite 下跳过，或在测试中用应用层锁兜底
- 边界值测试应覆盖 Pydantic Schema 校验层和业务逻辑层两层
- 测试数据使用 fixtures 创建，测试后清理，不污染其他测试
- 每个测试用例应独立可重复运行，不依赖执行顺序

---

## SEC-REFORM-05: Token 存储改用 HttpOnly Cookie

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-05 |
| 优先级 | P0 |
| 类型 | 安全修复 |
| 预估工作量 | 2天 |
| 关联需求 | SEC-P2-01（Token HttpOnly Cookie 安全存储） |
| Phase 1 依赖 | API-REFORM-01（401/403 区分已影响前端拦截器逻辑） |

### 需求描述

完善 Token 安全存储方案：后端已在 Phase 1 中实现 HttpOnly Cookie 设置（login/refresh 接口），但前端仍将 Token 存储在 localStorage，需完成前端适配，彻底消除 XSS 窃取 Token 的风险。

### 当前实现状态（代码核查）

| 维度 | 已实现 | 缺失/缺陷 |
|------|--------|----------|
| 后端 Cookie 设置 | ✅ login 接口设置 `access_token` + `refresh_token` HttpOnly Cookie | — |
| 后端 Cookie 读取 | ✅ `get_current_user` 优先从 Cookie 读取 Token | — |
| 后端 Cookie 清除 | ✅ logout 接口清除两个 Cookie | — |
| 前端请求携带 | ✅ `withCredentials: true` 已配置 | — |
| 前端 localStorage | ❌ 仍存储 Token 和用户信息 | 需清除 localStorage 中的 Token |
| 前端 401 拦截 | ✅ 已区分 401/403 处理 | — |
| CSRF 防护 | ❌ 缺失 | Cookie 认证必须加 CSRF 防护 |

### 前后端协作技术方案

**1. Token 传递架构变更**

```
之前：前端 localStorage → Authorization Header → 后端验证
现在：浏览器自动携带 HttpOnly Cookie → 后端从 Cookie 读取 → 验证
```

- 后端 `get_current_user` 已支持从 Cookie 读取（`request.cookies.get("access_token")`），也兼容 Header 传递
- 前端 `api.ts` 已配置 `withCredentials: true`，Cookie 会自动携带
- 前端不再需要从 localStorage 读取 Token 放入 Authorization Header

**2. Cookie 属性配置**

| 属性 | 值 | 说明 |
|------|-----|------|
| HttpOnly | true | 禁止 JavaScript 访问 |
| Secure | !DEBUG | 生产环境启用 HTTPS Only |
| SameSite | Lax | 防止 CSRF（大部分场景） |
| Path | / | 全站有效 |
| Max-Age | access: 30min / refresh: 7d | 过期时间 |

**3. CSRF 防护方案**

由于使用 Cookie 认证，必须防护 CSRF 攻击：

- 采用 **Double Submit Cookie** 模式：
  1. 后端在登录时额外设置一个非 HttpOnly 的 CSRF Token Cookie（`csrf_token`）
  2. 前端从 Cookie 读取 `csrf_token`，在每个 mutating 请求（POST/PUT/DELETE）的 Header `X-CSRF-Token` 中携带
  3. 后端中间件比对 Cookie 中的 `csrf_token` 与 Header 中的值是否一致
- GET 请求无需 CSRF 校验（幂等）
- SameSite=Lax 已提供基础防护，Double Submit Cookie 作为纵深防御

**4. CORS 配置调整**

当前 `allow_credentials=True` + `allow_origins=settings.cors_origins_list`，需确保：
- `allow_origins` 不能包含 `*`（与 credentials 冲突），必须为具体域名列表
- 生产环境 CORS 仅允许前端域名

### 验收标准

1. 前端 localStorage 中不再存储 Token（access_token / refresh_token），仅保留非敏感用户信息（userInfo、role）
2. 所有 API 请求通过 Cookie 自动携带 Token，不再依赖 Authorization Header
3. CSRF 防护生效：POST/PUT/DELETE 请求缺少 `X-CSRF-Token` Header 时返回 403
4. 登录成功后后端设置 `csrf_token` Cookie（非 HttpOnly），前端读取后在 mutating 请求中携带
5. 生产环境 CORS 仅允许指定前端域名，不含通配符

### 影响范围

- `frontend/src/stores/authStore.ts` — 移除 Token 存储，仅保留 userInfo
- `frontend/src/services/api.ts` — 请求拦截器不再注入 Authorization Header；添加 CSRF Token Header
- `frontend/src/pages/Login/index.tsx` — 登录成功后不再存 Token 到 localStorage
- `backend/app/core/middleware.py` — 新增 CSRF 校验中间件
- `backend/app/api/v1/auth.py` — 登录时设置 csrf_token Cookie
- `backend/app/main.py` — 注册 CSRF 中间件；收紧 CORS allow_methods

### 技术约束

- 后端 `get_current_user` 保持 Cookie + Header 双通道兼容，便于 API 测试工具使用
- CSRF Token 使用 `secrets.token_hex(32)` 生成，存储在 Cookie 中（非 HttpOnly，前端需读取）
- CSRF 校验中间件仅对 mutating 方法（POST/PUT/DELETE/PATCH）生效，GET/HEAD/OPTIONS 跳过
- WebSocket 连接不经过 CSRF 中间件（已通过 JWT 认证保护）
- 开发环境（DEBUG=True）可跳过 CSRF 校验，降低开发摩擦

---

## SEC-REFORM-06: 密码强度校验 + 登录限流

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-06 |
| 优先级 | P1 |
| 类型 | 安全修复 |
| 预估工作量 | 0.5天 |
| 关联需求 | SEC-P1-01（密码强度校验）、SEC-P1-02（登录失败限流） |
| Phase 1 依赖 | 无 |

### 需求描述

经代码核查，**密码强度校验和登录限流均已在 Phase 1 中实现**。本需求定义为**验收确认 + 前端密码规则提示 + 限流参数可配置化**。

### 当前实现状态（代码核查）

| 功能 | 位置 | 状态 | 待完善 |
|------|------|------|--------|
| 密码强度校验 | `schemas/auth.py:23-32` `validate_password_strength` | ✅ 已实现 | 前端注册页无规则提示 |
| 登录限流 | `api/v1/auth.py:16-17` `MAX_LOGIN_ATTEMPTS=5, LOCK_DURATION_MINUTES=15` | ✅ 已实现 | 限流参数硬编码 |
| 账户锁定 | `auth.py:65-82` | ✅ 已实现 | — |
| 手机号脱敏 | `auth.py:213-215` `mask_phone` | ✅ 已实现 | — |

### 密码规则定义

当前后端校验规则（`schemas/auth.py`）：

| 规则 | 校验逻辑 | 错误提示 |
|------|---------|---------|
| 最小长度 | `len(v) < 8` | 密码长度至少8位 |
| 包含小写字母 | `re.search(r"[a-z]", v)` | 密码必须包含小写字母 |
| 包含大写字母 | `re.search(r"[A-Z]", v)` | 密码必须包含大写字母 |
| 包含数字 | `re.search(r"\d", v)` | 密码必须包含数字 |

### 限流参数定义

当前后端限流参数（`api/v1/auth.py`）：

| 参数 | 当前值 | 说明 |
|------|--------|------|
| MAX_LOGIN_ATTEMPTS | 5 | 连续登录失败次数上限 |
| LOCK_DURATION_MINUTES | 15 | 锁定持续时间（分钟） |

### 验收标准

1. 后端密码强度校验生效（已实现），注册时弱密码被拒绝
2. 后端登录限流生效（已实现），5 次失败后锁定 15 分钟
3. 前端注册页面展示密码规则提示（至少8位、含大小写字母和数字）
4. 前端登录页面提示剩余尝试次数（后端已返回"还剩X次尝试机会"）
5. 限流参数 `MAX_LOGIN_ATTEMPTS` 和 `LOCK_DURATION_MINUTES` 从 `PlatformConfig` 读取，管理员可在后台配置

### 影响范围

- `frontend/src/pages/Register/index.tsx` — 添加密码规则提示
- `frontend/src/pages/Login/index.tsx` — 展示剩余尝试次数提示（已有后端返回信息）
- `backend/app/api/v1/auth.py` — 限流参数从配置读取而非硬编码

### 技术约束

- 密码规则提示使用 Ant Design Form 的 `extra` 或 `help` 属性，实时展示规则满足状态
- 限流参数配置化时，需考虑 PlatformConfig 尚未初始化的场景（使用默认值兜底）
- 不修改现有密码校验逻辑，仅做前端提示和参数配置化

---

## SEC-REFORM-07: XSS 防护（输入过滤 + 输出转义）

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-07 |
| 优先级 | P0 |
| 类型 | 安全修复 |
| 预估工作量 | 2天 |
| 关联需求 | 安全审计高危漏洞（XSS 风险） |
| Phase 1 依赖 | SEC-REFORM-03（WebSocket 认证已防伪造消息） |

### 需求描述

对用户输入（评价内容、备注、店铺名称、商品描述等）实施输入过滤，对所有用户生成的数据在前端展示时实施输出转义，防止 XSS 攻击。

### 当前防护状态（代码核查）

| 维度 | 已实现 | 缺失 |
|------|--------|------|
| CSP 响应头 | ✅ SecurityHeadersMiddleware 已设置 CSP | CSP 中 `unsafe-inline` 和 `unsafe-eval` 仍允许（React 需要） |
| X-XSS-Protection | ✅ 已设置 `1; mode=block` | — |
| X-Content-Type-Options | ✅ 已设置 `nosniff` | — |
| 后端输入过滤 | ❌ 评价内容、备注等未做 HTML 标签过滤 | 需添加 |
| 后端输出转义 | ❌ API 返回的用户内容未转义 | 需添加 |
| 前端输出转义 | ⚠️ React JSX 默认转义，但 `dangerouslySetInnerHTML` 使用需排查 | 需排查 |

### 输入过滤规则

以下字段需在 Pydantic Schema 层进行输入过滤：

| 字段 | 所属 Schema | 过滤规则 |
|------|------------|---------|
| `content` | ReviewCreate | 剥离 HTML 标签，仅保留纯文本 |
| `remark` | OrderCreate | 剥离 HTML 标签，仅保留纯文本 |
| `name` | ShopInfo / Product | 剥离 `<script>` 等危险标签，保留基本文本 |
| `description` | Product | 剥离 `<script>`/`<iframe>` 等危险标签 |
| `notice` | ShopInfo | 剥离危险标签 |
| `nickname` | UpdateUserRequest | 剥离所有 HTML 标签 |

过滤策略：
- **纯文本字段**（content、remark、nickname）：使用 `bleach.clean(text, tags=[], strip=True)` 移除所有 HTML
- **允许有限格式的字段**（description、notice）：保留 `<p>`、`<br>`、`<b>`、`<i>` 等安全标签
- **所有字段**：移除 `javascript:` 协议、`on*` 事件属性

### 输出转义策略

| 层级 | 策略 | 实现 |
|------|------|------|
| 前端 React | JSX 默认转义 | 确认不使用 `dangerouslySetInnerHTML` |
| 后端 API | JSON 序列化天然转义 `"` 和 `\` | 确认无 HTML 响应 |
| 前端特殊场景 | 排查 `dangerouslySetInnerHTML` | 如有，改用纯文本渲染 |

### 验收标准

1. 后端 Pydantic Schema 层添加输入过滤 validator，HTML 标签被剥离或净化
2. 前端代码中无 `dangerouslySetInnerHTML` 使用（全局搜索确认）
3. XSS 攻击测试：提交 `<script>alert('xss')</script>` 作为评价内容，存储和展示时不执行脚本
4. XSS 攻击测试：提交 `javascript:alert('xss')` 作为备注，不触发脚本执行
5. 正常内容（含中文、emoji、换行符）不受影响

### 影响范围

- `backend/app/schemas/review.py` — 评价内容过滤
- `backend/app/schemas/order.py` — 订单备注过滤
- `backend/app/schemas/shop.py` — 店铺名称/描述/公告过滤
- `backend/app/schemas/auth.py` — 昵称过滤
- `backend/requirements.txt` — 新增 `bleach` 依赖
- `frontend/src/` — 全局搜索排查 `dangerouslySetInnerHTML`

### 技术约束

- 使用 `bleach` 库进行 HTML 过滤，它是 Python 生态最成熟的 XSS 过滤库
- 过滤逻辑放在 Pydantic Schema 的 `field_validator` 中，与现有校验逻辑一致
- 过滤在写入数据库前执行（防御存储型 XSS），而非仅在输出时转义
- 前端 React 的 JSX 默认对变量进行 HTML 转义（`{variable}` 不会执行 HTML），这是天然防线
- 不使用自定义正则过滤，正则难以覆盖所有 XSS 变体

---

## SEC-REFORM-08: 敏感日志脱敏

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | SEC-REFORM-08 |
| 优先级 | P1 |
| 类型 | 安全修复 |
| 预估工作量 | 1天 |
| 关联需求 | SEC-P1-03（全局敏感日志脱敏） |
| Phase 1 依赖 | 无 |

### 需求描述

对日志中的敏感信息（手机号、金额、身份证号等）进行脱敏处理，防止日志泄露导致用户隐私或资金信息暴露。

### 当前脱敏状态（代码核查）

| 数据类型 | 当前处理 | 问题 |
|---------|---------|------|
| 手机号 | ✅ `mask_phone()` 已在 auth.py 中使用 | 仅 auth 模块使用，其他模块日志中仍输出完整手机号 |
| 金额 | ❌ 完整输出 | 如 `logger.info(f"Payment processed: amount={order.total_amount}")` |
| 用户ID | ⚠️ 直接输出 | 用户 ID 本身非敏感，但关联金额后构成风险 |
| 密码 | ✅ 从未日志输出 | — |

### 脱敏规则

| 数据类型 | 脱敏规则 | 示例 |
|---------|---------|------|
| 手机号 | 中间4位替换为 `****` | `138****1234` |
| 金额 | 保留整数位，小数位替换为 `**` | `128.**` |
| 身份证号 | 中间8位替换为 `********` | `110***********1234` |
| 银行卡号 | 保留后4位，其余替换为 `****` | `****1234` |
| 邮箱 | `@` 前仅保留首尾字符 | `t***e@example.com` |

### 验收标准

1. `backend/app/utils/sanitize.py` 中提供通用脱敏函数：`mask_phone`、`mask_amount`、`mask_id_card`、`mask_bank_card`、`mask_email`
2. 所有 `logger.info`/`logger.warning`/`logger.error` 中的手机号使用 `mask_phone` 脱敏
3. 金融相关日志中的金额使用 `mask_amount` 脱敏
4. 全局搜索确认无日志直接输出完整的手机号或金额
5. 现有 `auth.py` 中的 `mask_phone` 替换为通用版本

### 影响范围

- `backend/app/utils/sanitize.py` — 新增文件，通用脱敏工具
- `backend/app/api/v1/auth.py` — 替换内联 `mask_phone` 为通用版本
- `backend/app/services/finance.py` — 金额日志脱敏
- `backend/app/services/order_service.py` — 订单相关日志脱敏
- `backend/app/api/v1/wallet.py` — 钱包相关日志脱敏
- 其他包含 logger 调用的文件 — 手机号/金额脱敏

### 技术约束

- 脱敏函数为纯函数，无副作用，方便单元测试
- 脱敏在日志输出时执行，不影响数据库存储和 API 返回的原始数据
- `mask_amount` 仅脱敏日志中的金额，数据库和接口仍返回精确金额
- 异常日志（`logger.error`）中如果包含请求参数，同样需要脱敏
- 现有 `auth.py` 的 `mask_phone` 函数迁移到 `sanitize.py`，auth.py 改为 import

---

## UX-REFORM-01: 图片上传集成到 Review.tsx / Products.tsx

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | UX-REFORM-01 |
| 优先级 | P1 |
| 类型 | 用户体验 |
| 预估工作量 | 0.5天 |
| 关联需求 | U-P1-04（评价含图片）、S-P0-03（商品图片上传） |
| Phase 1 依赖 | 无 |

### 需求描述

经代码核查，**图片上传功能已在 Review.tsx 和 Products.tsx 中完整实现**。本需求定义为**验收确认 + 细节优化**。

### 当前实现状态（代码核查）

| 页面 | 图片上传 | 状态 | 待优化 |
|------|---------|------|--------|
| Review.tsx | Upload 组件 + `uploadApi.upload` + 预览/删除 | ✅ 已实现 | — |
| Products.tsx | Upload 组件 + `handleImageUpload` | ✅ 已实现 | — |
| 后端 upload.py | POST /upload + 白名单 + 文件签名验证 | ✅ 已实现 | — |
| 后端 review.py | images 字段 JSON 序列化存储 | ✅ 已实现 | — |

### 验收标准

1. 评价页面可上传最多 3 张图片，支持预览和删除
2. 商家商品管理页面可上传商品主图，支持替换
3. 上传限制：仅 jpg/png/gif/webp 格式，单文件 ≤ 5MB
4. 评价图片在商家详情页正确展示
5. 商品图片在首页和商家详情页正确展示

### 影响范围

- 无需修改，功能已完整实现

### 技术约束

- 确认 `uploadApi` 和 `upload.py` 的白名单一致（jpg/png/gif/webp）
- 确认图片 URL 在前端正确拼接（相对路径 + 后端静态文件服务）

---

## UX-REFORM-02: 管理员订单管理页 admin/Orders.tsx

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | UX-REFORM-02 |
| 优先级 | P1 |
| 类型 | 管理功能 |
| 预估工作量 | 1天 |
| 关联需求 | A-P1-03（全局订单管理） |
| Phase 1 依赖 | 无 |

### 需求描述

经代码核查，**管理员订单管理页已存在基础实现**（`admin/Orders.tsx` + `admin.py` 的 `list_all_orders`/`get_admin_order_detail` 接口）。本需求定义为**功能增强**：补充订单详情中的用户信息、异常订单筛选、导出能力。

### 当前实现状态（代码核查）

| 功能 | 已实现 | 缺失 |
|------|--------|------|
| 订单列表 + 分页 | ✅ Table + Pagination | — |
| 状态筛选 Tabs | ✅ 7 种状态 Tab | — |
| 订单详情弹窗 | ✅ Descriptions 组件 | 缺少用户信息展示 |
| 订单号、商家、金额、状态 | ✅ | — |
| 后端 list_all_orders API | ✅ N+1 问题待 PERF-REFORM-01 修复 | — |
| 后端 get_admin_order_detail API | ✅ 已查询用户信息 | 前端未展示 |
| 导出功能 | ❌ | 需新增 |
| 异常订单标记 | ❌ | 需新增 |

### 页面交互设计（增强版）

**1. 订单列表 — 增强筛选**

```
┌──────────────────────────────────────────────────────┐
│ 订单管理                                              │
│                                                      │
│ [全部] [待支付] [待接单] [备餐中] [待取餐] [配送中]    │
│ [已完成] [已取消]                                     │
│                                                      │
│ 筛选：[订单号搜索____] [商家搜索____] [日期范围__~__]  │  ← 新增
│                                                      │
│ ┌──────┬────────┬──────┬──────┬──────┬──────┬─────┐  │
│ │订单号│ 商家   │金额  │状态  │下单人│时间  │操作 │  │
│ ├──────┼────────┼──────┼──────┼──────┼──────┼─────┤  │
│ │...   │ ...    │¥28  │待支付│张*4  │5/19  │详情 │  │  ← 新增：下单人列
│ └──────┴────────┴──────┴──────┴──────┴──────┴─────┘  │
│                                                      │
│ 共 156 条                        [导出 Excel]         │  ← 新增：导出按钮
└──────────────────────────────────────────────────────┘
```

**2. 订单详情弹窗 — 增强用户信息**

```
┌──────────────────────────────────────┐
│  订单详情                             │
│                                      │
│  订单号：20260519143000001            │
│  商家：黄焖鸡米饭                     │
│  ── 下单用户 ──                       │  ← 新增
│  用户昵称：张三                        │
│  手机号：138****1234                  │  ← 脱敏展示
│  ── 订单信息 ──                       │
│  订单金额：¥28.00                     │
│  配送费：¥3.00                        │
│  收货地址：xxx路xxx号                  │
│  联系电话：138****1234                │  ← 脱敏展示
│  订单状态：[待支付]                    │
│  备注：不要辣                         │
│  创建时间：2026-05-19 14:30:00        │
│  ── 商品明细 ──                       │
│  黄焖鸡 × 1 - ¥25.00                 │
│  米饭 × 1 - ¥3.00                    │
└──────────────────────────────────────┘
```

### 验收标准

1. 订单列表新增"下单人"列（昵称脱敏展示），后端 API 已返回 `user_nickname`/`user_phone`
2. 订单详情弹窗展示下单用户信息（昵称 + 手机号脱敏），后端 `get_admin_order_detail` 已查询 User
3. 新增订单号和商家名搜索框，支持模糊搜索
4. 导出按钮可导出当前筛选条件下的订单列表为 CSV 文件
5. N+1 查询问题由 PERF-REFORM-01 统一修复

### 影响范围

- `frontend/src/pages/admin/Orders.tsx` — 主要修改文件
- `backend/app/api/v1/admin.py` — `list_all_orders` 添加用户信息字段、搜索参数
- `backend/app/schemas/order.py` — OrderResponse 添加 `user_nickname`、`user_phone` 字段

### 技术约束

- 手机号在前端展示时使用脱敏（`138****1234`），后端 API 可返回完整手机号（管理员权限），脱敏在前端执行
- CSV 导出使用前端生成（前端已有筛选后的数据），不新增后端导出接口
- 搜索功能使用后端查询（`Order.order_no.contains(keyword)`），避免前端全量加载
- 导出字段：订单号、商家、金额、状态、下单人、创建时间

---

## DOC-REFORM-01: 更新测试报告覆盖账户/安全模块

### 基本信息

| 属性 | 值 |
|------|-----|
| 需求ID | DOC-REFORM-01 |
| 优先级 | P1 |
| 类型 | 文档质量 |
| 预估工作量 | 2天 |
| 关联需求 | 全局测试覆盖 |
| Phase 1 依赖 | Phase 1 全部完成后更新 |

### 需求描述

更新 `test-report.md`，使其反映当前测试覆盖状况，包括 Phase 1 和 Phase 2 新增的账户/安全模块测试。

### 当前问题

- 现有 `test-report.md` 写于账户系统和安全修复之前，声称 42/42 通过，但不覆盖最关键的功能
- Phase 1 完成后已有 250 测试通过，文档未更新
- 缺少账户/安全模块的专项测试报告

### 验收标准

1. `docs/test-report.md` 更新为当前版本，反映实际测试数量和通过率
2. 新增"账户/结算模块测试"章节，覆盖 F-P0-01~08 的测试结果
3. 新增"安全模块测试"章节，覆盖 SEC-P0-01~06 的测试结果
4. 新增"Phase 1 修复验证"章节，覆盖 SEC-REFORM-01~04、API-REFORM-01、CODE-REFORM-01 的测试结果
5. 标注各模块的测试覆盖率（高/中/低）

### 影响范围

- `docs/test-report.md` — 主要更新文件

### 技术约束

- 测试数据基于实际运行结果，不编造
- 测试覆盖率使用 pytest-cov 工具生成（如已安装），或基于文件覆盖估算
- 保留历史版本的测试结果作为对比参考

---

## 依赖关系与实施顺序

```
SEC-REFORM-07 (XSS防护)            ─┐
SEC-REFORM-08 (日志脱敏)            ─┤  可并行（独立安全修复）
SEC-REFORM-05 (HttpOnly Cookie)     ─┘
         ↓
SEC-REFORM-06 (密码+限流)           ← 小改动，可穿插
         ↓
PERF-REFORM-01 (N+1 修复)          ← 基础性能优化
         ↓
PERF-REFORM-02 (Redis 缓存)        ← 依赖 N+1 修复完成后再加缓存
PERF-REFORM-03 (路由懒加载)         ─┐
UX-REFORM-02 (管理员订单增强)       ─┤  可并行
UX-REFORM-01 (图片上传验收)         ─┤  仅验收确认
         ↓
TEST-REFORM-01 (并发+边界测试)      ← 依赖所有功能修复完成
DOC-REFORM-01 (测试报告更新)        ← 依赖测试完成
```

### 建议分组实施

| 批次 | 内容 | 预估工期 |
|------|------|---------|
| 第1批（并行） | SEC-REFORM-05 + SEC-REFORM-07 + SEC-REFORM-08 | 3天 |
| 第2批 | SEC-REFORM-06 + PERF-REFORM-01 + PERF-REFORM-02 | 4天 |
| 第3批（并行） | PERF-REFORM-03 + UX-REFORM-02 + UX-REFORM-01 | 2天 |
| 第4批 | TEST-REFORM-01 + DOC-REFORM-01 | 4天 |
| **合计** | | **~13个工作日** |

---

## 关键发现：Phase 1 中已提前完成的部分 Phase 2 内容

经代码核查，以下 Phase 2 优化项已在 Phase 1 实施过程中**提前完成**：

| 优化项 | 原Phase 2 定位 | 实际状态 | 剩余工作 |
|--------|---------------|---------|---------|
| 密码强度校验 | SEC-REFORM-06 | ✅ 已实现 | 前端提示 + 参数配置化 |
| 登录限流 | SEC-REFORM-06 | ✅ 已实现 | 参数配置化 |
| HttpOnly Cookie（后端） | SEC-REFORM-05 | ✅ 已实现 | 前端适配 + CSRF |
| 图片上传（Review.tsx） | UX-REFORM-01 | ✅ 已实现 | 仅验收 |
| 图片上传（Products.tsx） | UX-REFORM-01 | ✅ 已实现 | 仅验收 |
| 管理员订单管理页 | UX-REFORM-02 | ✅ 基础已实现 | 功能增强 |

这意味着 Phase 2 的实际开发量从原预估的 20 天降至约 13 天。

---

## 文件变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-05-19 | 初始版本，定义 Phase 2 全部 11 项增量需求 |
