# FuYellowBlueRed 项目全面分析与优化方案

> 分析日期: 2026-05-19 | 分析范围: 全栈（前端 + 后端 + 文档 + 架构 + 质量）
> 版本: v2.0 — 整合代码审查 + 文档/需求差距分析

---

## 一、项目概况

| 维度 | 状态 |
|------|------|
| 项目名称 | FuYellowBlueRed - 开源外卖配送平台 |
| 技术栈 | 前端: React + Ant Design + Zustand + Vite / 后端: FastAPI + SQLAlchemy + Redis |
| 代码规模 | 前端 ~65 TS/TSX 文件 / 后端 ~77 Python 文件 |
| 数据库 | SQLite (开发) / MySQL (生产) / 20 张数据表 |
| 部署 | Docker Compose (前端 + 后端 + Redis + 备份) |
| API 端点 | 61 个已实现 |
| 数据模型 | 18 个已实现 |
| 文档 | 4 版 PRD + 安全审计 + 架构评审 + 任务分解 + 测试报告 + 开发计划 |
| 当前阶段 | Phase 1 MVP + Phase 2 架构改进 已完成 |

### 需求实现进度总览

| 优先级 | 实现率 | 说明 |
|--------|--------|------|
| **P0 核心功能** | ~70% | 关键缺失：支付倒计时 + 订单超时自动取消 |
| **P1 体验功能** | ~40% | 前端钱包页缺失、管理员订单管理缺失、通知未实现 |
| **P2 增值功能** | ~5% | 优惠券、收藏、客服等均未实现 |
| **账户/结算 P0** | 8/8 (100%) | 钱包支付、佣金计算、退款回滚等全部完成 |
| **安全 P0** | 6/6 (100%) | 支付幂等、充值限额、文件上传白名单等全部修复 |
| **安全 P1** | 0/6 (0%) | 密码强度、登录限流、日志脱敏等均未实现 |
| **安全 P2** | 0/6 (0%) | 安全响应头、审计日志、依赖扫描等均未实现 |

---

## 二、需求维度分析

### 2.1 需求完整性评估（基于 prd-final.md v4.0 对标）

#### 已完整实现的功能 ✅

**消费者 P0:**
- U-P0-01: 用户取消订单 (PUT /orders/{id}/cancel + Orders.tsx 取消按钮)
- U-P0-03: 图片上传 (POST /upload + 文件签名验证 + 白名单)
- U-P0-04: 商家真实详情数据 (monthly_sales, min_order_amount, delivery_fee 等)
- U-P0-05: 购物车清空 (DELETE /cart/shop/{shop_id} + Cart.tsx 清空按钮)
- U-P0-06: 订单状态实时更新 (Orders.tsx 5秒轮询)

**消费者 P1:**
- U-P1-01: 用户资料编辑 (PUT /users/me + Profile.tsx)
- U-P1-02: 地址管理 (完整 CRUD + Addresses.tsx)
- U-P1-03: 订单详情页 (Timeline + OrderResponse)

**商家 P0:**
- S-P0-01: 商家仪表盘 (GET /shop/my/stats + shop/Dashboard.tsx)
- S-P0-02: 商家订单详情 (GET /shop/my/orders/{id} + 详情弹窗)

**商家 P1:**
- S-P1-01: 商家信息编辑 (PUT /shop/my + shop/ShopInfo.tsx)

**骑手 P0/P1:**
- R-P0-01: 配送完成确认 (PUT /rider/orders/{id}/deliver)
- R-P1-01: 订单详情查看 (rider/Orders.tsx 详情弹窗)
- R-P1-03: 骑手数据仪表盘 (GET /rider/earnings/summary + rider/Earnings.tsx)

**管理员 P1:**
- A-P1-02: 商家管理审核 (GET /admin/shop/pending + admin/Shops.tsx)

**账户/结算 P0 (全部完成):**
- F-P0-01 ~ F-P0-08: 钱包余额支付、唯一交易ID、自动佣金计算、骑手收益结算、资金流水记录、退款回滚、平台佣金记录、可配置结算参数

**安全 P0 (全部修复):**
- SEC-P0-01 ~ SEC-P0-06: 支付幂等、充值限额、文件上传白名单、JWT密钥环境变量强制、仅管理员充值、事务一致性

#### 部分实现的功能 ⚠️

| 需求ID | 描述 | 已实现 | 缺失部分 |
|--------|------|--------|----------|
| U-P1-04 | 评价含图片 | Review.tsx 有评分 | 图片上传未集成 |
| U-P1-05 | 首页真实数据 | Home.tsx 有筛选 | 分类筛选待优化 |
| U-P1-06 | 搜索增强 | 关键词搜索可用 | 搜索历史未实现 |
| U-P2-03 | 用户钱包 | 后端API完整 | **前端钱包页缺失** |
| S-P0-03 | 商品图片上传 | POST /upload 存在 | Products.tsx 未集成 |
| R-P0-02 | 骑手提现 | API 存在 | rider/Withdraw.tsx 待完善 |
| A-P1-01 | 管理仪表盘 | 基础数据展示 | 趋势图表未实现 |

#### 未实现的关键功能 ❌

**P0 关键缺失：**
| 需求ID | 描述 | 影响 |
|--------|------|------|
| **U-P0-02** | **支付倒计时（15分钟）+ 订单超时自动取消** | **最关键缺失**：前端倒计时组件 + 后端调度任务均未实现 |

**P1 体验缺失：**
| 需求ID | 描述 |
|--------|------|
| S-P1-02 | 商家拒绝订单须填写原因 |
| S-P1-03 | 新订单通知（需 WebSocket 或轮询） |
| R-P1-02 | 一键联系用户 (tel: 链接) |
| A-P1-03 | 管理员订单管理页 (admin/Orders.tsx 缺失) |

**P1 安全缺失（0/6 未实现）：**
| 需求ID | 描述 |
|--------|------|
| SEC-P1-01 | 密码强度校验（8+字符，字母+数字） |
| SEC-P1-02 | 登录失败限流（5次失败→15分钟锁定） |
| SEC-P1-03 | 敏感日志脱敏（手机号/金额/身份证） |
| SEC-P1-06 | 账户异常自动锁定 |

**P2 增值功能缺失：**
- U-P2-01 商家收藏、U-P2-02 优惠券系统、U-P2-04 客服中心、U-P2-05 加购动画、U-P2-06 暗黑模式
- SEC-P2-01 Token存储升级httpOnly Cookie、SEC-P2-02 安全响应头(CSP等)、SEC-P2-03 操作审计日志、SEC-P2-05 依赖安全扫描、SEC-P2-06 多设备登录管理

### 2.2 前后端实现差距（API 已就绪但前端缺失）

这是当前最突出的交付瓶颈——后端能力已就绪但前端页面未对接：

| 后端 API | 前端状态 | 优先级 |
|----------|----------|--------|
| 钱包余额/充值/提现 (GET/POST /wallet/*) | **用户钱包页完全缺失** | P0 |
| 骑手提现 API | rider/Withdraw.tsx 待完善 | P1 |
| 图片上传 POST /upload | Review.tsx / Products.tsx 未集成 | P1 |
| 管理员订单查询 | admin/Orders.tsx 缺失 | P1 |

---

## 三、开发维度分析

### 3.1 严重问题（P0 - 必须修复）

#### 3.1.1 API 路由与 Service 层重复代码
**位置**: `backend/app/api/v1/orders.py` vs `backend/app/services/order_service.py`

两处代码几乎完全重复（get_cart、add_to_cart、create_order 等），违反 DRY 原则：
- API 路由中直接操作数据库，绕过 Service 层
- Service 层代码未被 API 路由调用
- 修改业务逻辑需要同步两处，极易遗漏

**修复方案**: API 路由统一调用 Service 层，删除路由中直接的 DB 操作

#### 3.1.2 N+1 查询问题
**位置**: 多个 API 和 Service 文件

```python
# orders.py get_cart: 对每个购物车项逐个查询 product 和 shop
for item in cart_items:
    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    shop_result = await db.execute(select(Shop).where(Shop.id == item.shop_id))
```

同样问题存在于 `list_orders`、`get_order_detail`、`cancel_order` 等接口。

**修复方案**: 使用 `selectinload`/`joinedload` 预加载关联数据，或批量 `IN` 查询

#### 3.1.3 订单号生成存在碰撞风险
**位置**: `orders.py` L262, `order_service.py` L196

```python
order_no = datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(100000, 999999)}"
```

高并发下秒级精度 + 6位随机数碰撞概率高，且未做唯一性校验。

**修复方案**: 使用 UUID 或雪花算法，或在数据库层加唯一约束 + 重试

### 3.2 高优先级问题（P1）

#### 3.2.1 金额精度使用 Float
**位置**: `models.py` 所有金额字段

```python
balance: Mapped[float] = mapped_column(Float, default=0.0)  # 精度丢失风险
total_amount: Mapped[float] = mapped_column(Float, nullable=False)
```

金融场景必须使用 `Numeric(10, 2)` 或 `DECIMAL`，Float 存在精度丢失。

**修复方案**: 全局替换 `Float` → `Numeric(10, 2)`，添加 Alembic 迁移

#### 3.2.2 缺少数据库事务保护
**位置**: `orders.py` create_order, cancel_order 等关键操作

创建订单时涉及扣库存、清购物车、创建订单项，但未使用 `SELECT FOR UPDATE` 锁定库存行，高并发下可能超卖。

**修复方案**: 对库存扣减使用 `with_for_update()` 行锁

#### 3.2.3 WebSocket 无认证
**位置**: `main.py` websocket_endpoint

```python
@app.websocket("/ws/{channel}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, channel: str, user_id: str):
    await websocket.accept()  # 无需认证即可连接
```

任何人可冒充任意 user_id 连接 WebSocket，接收/发送消息。

**修复方案**: 连接时验证 JWT Token

#### 3.2.4 前端 Token 存储不安全
**位置**: `frontend/src/stores/authStore.ts`

使用 `zustand/persist` 将认证信息存入 localStorage，易受 XSS 攻击。

**修复方案**: Token 存入 HttpOnly Cookie，前端仅存非敏感用户信息

### 3.3 中优先级问题（P2）

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| 1 | `require_role` 返回 401 而非 403 | `deps/auth.py` L60 | 权限不足与未认证混淆 |
| 2 | API 响应结构不统一 | `schemas/base.py` vs 各路由 | 部分用 `ResponseSchema`，部分直接返回 |
| 3 | 前端无请求取消/防抖 | 各页面组件 | 快速点击重复提交 |
| 4 | 前端缺少 ErrorBoundary 覆盖 | `App.tsx` | 组件崩溃白屏 |
| 5 | CORS 配置 `allow_methods=["*"]` | `main.py` L109 | 安全性不足 |
| 6 | 密码强度无校验 | `auth.py` 注册 | 弱密码风险 |
| 7 | SQLAlchemy pool_size=20 对 SQLite 无效 | `database.py` L8 | 配置误导 |
| 8 | 缺少 API 请求参数长度限制 | 各路由 | DoS 风险 |

---

## 四、测试维度分析

### 4.1 后端测试现状

| 测试文件 | 覆盖模块 | 评估 |
|---------|---------|------|
| test_auth.py | 认证注册登录 | 基础覆盖 |
| test_orders.py | 订单CRUD | 基础覆盖 |
| test_shop.py | 商家模块 | 基础覆盖 |
| test_rider.py | 骑手模块 | 基础覆盖 |
| test_admin.py | 管理后台 | 基础覆盖 |
| test_finance.py | 金融模块 | 基础覆盖 |
| test_coupons.py | 优惠券 | 基础覆盖 |
| test_wallet.py | 钱包 | 基础覆盖 |
| test_review.py | 评价 | 基础覆盖 |
| test_phase2.py | 架构改进 | 验证性测试 |
| test_bugfix.py | Bug修复 | 验证性测试 |
| test_cycle*.py | 迭代测试 | 回归测试 |

### 4.2 测试缺失项

1. **并发测试**: 金融操作（支付、退款、提现）无并发场景测试
2. **边界测试**: 缺少金额边界（0元、负数、超大数）、库存边界（0库存、负库存）
3. **集成测试**: 订单全流程（创建→支付→接单→配送→完成→结算）缺少端到端测试
4. **安全测试**: 无 SQL 注入、XSS、CSRF、越权访问测试
5. **性能测试**: 无压力测试、无慢查询测试

### 4.3 前端测试现状

仅有 5 个测试文件，覆盖率极低：
- `auth.test.ts` - 认证相关
- `CountdownTimer.test.tsx` - 倒计时组件
- `notification.test.ts` - 通知
- `order.test.ts` - 订单
- `ThemeContext.test.tsx` - 主题

**缺失**: 页面组件测试、Hooks 测试、API 集成测试、E2E 测试

---

## 五、安全维度分析

| 风险等级 | 问题 | 描述 |
|---------|------|------|
| **高危** | 默认 SECRET_KEY | 生产环境可能仍使用默认密钥 |
| **高危** | WebSocket 无认证 | 任何人可冒充连接 |
| **高危** | XSS 风险 | 用户输入（评价、备注等）未做 HTML 转义 |
| **高危** | 金额 Float 精度 | 可能导致资金计算误差 |
| **中危** | Token 存 localStorage | 易受 XSS 窃取 |
| **中危** | 无速率限制白名单 | 管理接口应有更严格的限流 |
| **中危** | 缺少 CSRF 防护 | Cookie 认证方式需 CSRF 保护 |
| **低危** | 错误信息泄露 | 部分异常返回内部堆栈信息 |
| **低危** | CORS 配置过宽 | allow_methods=["*"] |

---

## 六、性能维度分析

### 6.1 后端性能问题

1. **N+1 查询**: 购物车、订单列表、商家详情等接口存在 N+1 问题
2. **无分页优化**: `list_orders` 查询总数和列表串行执行，应并行
3. **Redis 缓存未利用**: 商家列表、商品信息等热点数据无缓存
4. **SQLite 限制**: 不支持并发写入，生产环境必须切换 MySQL
5. **无连接池监控**: pool_size=20 但无监控和告警

### 6.2 前端性能问题

1. **无代码分割**: 所有页面组件在 App.tsx 中静态导入，首屏加载慢
2. **无图片懒加载**: 商家/商品图片全部直接加载
3. **无虚拟列表**: 长列表（订单、商品）未使用虚拟滚动
4. **轮询代替推送**: 订单状态使用前端轮询而非 WebSocket

---

## 七、架构维度分析

### 7.1 架构优点

- 分层架构清晰: API → Service → Model
- 统一异常处理体系
- Prometheus 监控集成
- 配置分层管理
- API 版本控制
- 账户/结算系统设计完善：资金流水、可配置参数、验证标准齐全

### 7.2 架构问题

1. **API 与 Service 重复**: Service 层形同虚设，大量逻辑直接写在路由中
2. **单文件模型**: 20+ 个模型全在 `models.py` 一个文件中，应拆分
3. **缺少 DTO 转换层**: Schema 直接 `model_validate` ORM 对象，内部字段可能泄露
4. **定时任务简陋**: 60s 轮询无分布式锁，多实例会重复执行
5. **WebSocket 广播模式**: 应改为按用户定向推送

---

## 七-B、文档与需求追溯维度分析

### 7B.1 文档清单与质量评估

| 文件 | 大小 | 状态 | 评估 |
|------|------|------|------|
| `prd-final.md` (v4.0) | 23.6 KB | ✅ 权威版本 | 需求+实现状态追踪完整，唯一权威来源 |
| `prd-v2.md` (v2.0) | 31.7 KB | ⚠️ 历史版本 | 含账户/结算+安全需求，已被 final 合并 |
| `prd-v3.md` (v3.0) | 14.7 KB | ⚠️ 历史版本 | 代码审计更新，已被 final 合并 |
| `requirements.md` (v2.0) | 19.6 KB | ⚠️ 历史版本 | 原始需求规格，已被 PRD 演进取代 |
| `security_audit_report.md` | 16.6 KB | ✅ 有效 | 30 个漏洞详尽记录，含修复方案 |
| `architecture-review.md` | 7.2 KB | ⚠️ 仅为建议 | 优化建议均未落地实施 |
| `task-breakdown.md` | 27.1 KB | ❌ 过时 | 103 任务但不含账户/安全 Sprint |
| `test-report.md` | 11.5 KB | ❌ 过时 | 42/42 通过，但不含账户/安全测试 |
| `development-plan.md` | 14.6 KB | ⚠️ 部分过时 | Sprint 命名与 PRD 不一致 |
| `home-page.html` | 0.7 KB | ❌ 非文档 | Vite 开发模板，不应放在 docs |
| `login-page.html` | 0.7 KB | ❌ 非文档 | 与 home-page.html 完全相同 |

### 7B.2 文档核心问题

1. **PRD 版本冗余**: 4 个 PRD 版本共存，开发人员可能混淆权威来源。应仅保留 `prd-final.md`，其余归档或删除
2. **任务分解过时**: `task-breakdown.md` 在账户/安全 Sprint 之前编写，不覆盖 61 个 API 和 18 个模型的当前状态
3. **测试报告过时**: 写于账户系统和安全修复之前，声称 100% 通过率但不覆盖最关键的功能
4. **缺少运维文档**: 无部署指南、Docker Compose 使用说明、环境变量参考、运维手册
5. **缺少独立 API 文档**: FastAPI 自动生成 Swagger，但 docs 目录无独立 API 参考文档
6. **Sprint 命名不一致**: 开发计划用 "Sprint 0/1/2/Security"，PRD 用 "Sprint 1/Sec1/2/3"
7. **架构评审未落地**: 优化建议均停留在文档阶段，无跟踪、无实施计划

### 7B.3 文档演进链

```
requirements.md (v2.0) → prd-v2.md (+账户/安全) → prd-v3.md (+代码审计状态)
                                                            ↓
                                                      prd-final.md (v4.0) ← 权威版本
```

**建议**: 将 v2/v3/requirements 归档至 `docs/archive/`，仅保留 `prd-final.md` 作为当前唯一权威需求文档。

---

## 八、优化方案（按优先级排列）

### Phase 1: 紧急修复（1-2 周）

| # | 优化项 | 维度 | 影响 | 工作量 |
|---|--------|------|------|--------|
| 1 | 金额字段 Float → Numeric | 开发 | 金融安全 | 2天 |
| 2 | 订单号生成改用 UUID/雪花 | 开发 | 数据安全 | 0.5天 |
| 3 | WebSocket 添加认证 | 安全 | 安全 | 1天 |
| 4 | `require_role` 返回 403 | 开发 | 接口规范 | 0.5天 |
| 5 | 库存扣减加行锁 | 开发 | 并发安全 | 1天 |
| 6 | 删除 API 路由重复代码，统一调用 Service | 开发 | 代码质量 | 3天 |
| 7 | **实现支付倒计时 + 订单超时自动取消 (U-P0-02)** | 需求 | **最关键 P0 缺失** | 3天 |
| 8 | **实现用户钱包前端页面** | 需求 | 后端API已就绪，前端缺失 | 2天 |

### Phase 2: 质量提升（2-3 周）

| # | 优化项 | 维度 | 影响 | 工作量 |
|---|--------|------|------|--------|
| 1 | 修复所有 N+1 查询 | 开发 | 性能 | 3天 |
| 2 | 添加 Redis 缓存层 | 开发 | 性能 | 2天 |
| 3 | 前端路由懒加载 | 开发 | 性能 | 1天 |
| 4 | 添加并发测试 + 边界测试 | 测试 | 质量 | 3天 |
| 5 | Token 存储改用 HttpOnly Cookie | 安全 | 安全 | 2天 |
| 6 | 密码强度校验 + 登录限流 (SEC-P1-01/02) | 安全 | 安全 | 1天 |
| 7 | XSS 防护（输入过滤 + 输出转义） | 安全 | 安全 | 2天 |
| 8 | **敏感日志脱敏 (SEC-P1-03)** | 安全 | 安全 | 1天 |
| 9 | **图片上传集成到 Review.tsx / Products.tsx** | 需求 | 功能完整性 | 1天 |
| 10 | **管理员订单管理页 admin/Orders.tsx** | 需求 | 管理能力 | 2天 |
| 11 | **更新测试报告覆盖账户/安全模块** | 测试 | 文档质量 | 2天 |

### Phase 3: 架构优化 + 文档治理（3-4 周）

| # | 优化项 | 维度 | 影响 | 工作量 |
|---|--------|------|------|--------|
| 1 | 模型文件拆分 | 开发 | 可维护性 | 2天 |
| 2 | WebSocket 按用户定向推送 | 开发 | 功能完整性 | 2天 |
| 3 | 延迟队列替代轮询 | 开发 | 性能 | 3天 |
| 4 | 添加商品搜索（Elasticsearch/MySQL FT） | 需求 | 核心功能 | 3天 |
| 5 | 前端 E2E 测试 | 测试 | 质量 | 3天 |
| 6 | 管理后台数据导出 + 报表 | 需求 | 运营能力 | 3天 |
| 7 | **PRD 历史版本归档 (v2/v3/requirements → archive/)** | 文档 | 消除混淆 | 0.5天 |
| 8 | **更新 task-breakdown.md 覆盖当前 61 API / 18 模型** | 文档 | 任务追溯 | 2天 |
| 9 | **补充运维文档（部署指南、环境变量、Docker）** | 文档 | 运维效率 | 2天 |
| 10 | **清理非文档文件 (home-page.html, login-page.html)** | 文档 | 目录整洁 | 0.5天 |

---

## 九、关键代码改进示例

### 9.1 修复 N+1 查询（orders.py get_cart）

**Before:**
```python
for item in cart_items:
    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = product_result.scalar_one_or_none()
    shop_result = await db.execute(select(Shop).where(Shop.id == item.shop_id))
    shop = shop_result.scalar_one_or_none()
```

**After:**
```python
from sqlalchemy.orm import selectinload

stmt = select(CartItem).where(CartItem.user_id == user_id).options(
    selectinload(CartItem.product),
    selectinload(CartItem.shop),
)
result = await db.execute(stmt)
cart_items = result.scalars().all()
```

### 9.2 金额字段修复

**Before:**
```python
balance: Mapped[float] = mapped_column(Float, default=0.0)
```

**After:**
```python
from sqlalchemy import Numeric
balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
```

### 9.3 库存扣减加锁

**Before:**
```python
product = product_result.scalar_one_or_none()
product.stock -= quantity
```

**After:**
```python
stmt = select(Product).where(Product.id == product_id).with_for_update()
product = (await db.execute(stmt)).scalar_one_or_none()
if product.stock < quantity:
    raise BadRequestException("库存不足")
product.stock -= quantity
```

### 9.4 前端路由懒加载

**Before:**
```tsx
import UserHome from '@/pages/user/Home'
```

**After:**
```tsx
const UserHome = React.lazy(() => import('@/pages/user/Home'))
```

---

## 十、量化目标

| 指标 | 当前 | Phase 1 后 | Phase 2 后 | Phase 3 后 |
|------|------|-----------|-----------|-----------|
| API 响应时间 (P95) | ~300ms | ~200ms | ~100ms | ~80ms |
| N+1 查询数 | 15+ | 15+ | 0 | 0 |
| 后端测试覆盖率 | ~40% | ~45% | ~70% | ~85% |
| 前端测试覆盖率 | ~10% | ~10% | ~40% | ~60% |
| 安全漏洞 (高危) | 4 | 1 | 0 | 0 |
| 代码重复率 | ~25% | ~10% | ~5% | ~3% |
| 首屏加载时间 | ~3s | ~3s | ~1.5s | ~1s |
| **P0 需求实现率** | **~70%** | **~95%** | **~98%** | **100%** |
| **P1 需求实现率** | **~40%** | **~45%** | **~70%** | **~90%** |
| **安全 P1 实现率** | **0/6** | **1/6** | **4/6** | **6/6** |
| **测试报告时效性** | 过时 | 过时 | 已更新 | 已更新 |
| **文档完整度** | 中 | 中 | 高 | 高 |

---

## 十一、总结

FuYellowBlueRed 作为一个 MVP 阶段的外卖平台，**基本功能闭环已完成**，架构设计思路清晰（分层、版本控制、异常处理），账户/结算系统设计完善。但存在以下核心短板：

### 🔴 紧急风险（需立即处理）
1. **金融安全风险**: 金额精度(Float) + 库存并发(无行锁) 是最紧迫的问题
2. **P0 功能缺失**: 支付倒计时 + 订单超时自动取消是需求层面最关键的缺口
3. **前后端交付脱节**: 钱包/提现等后端 API 已就绪但前端页面缺失

### 🟡 重要问题（2-3 周内解决）
4. **代码质量债务**: API/Service 重复、N+1 查询影响可维护性和性能
5. **安全防护薄弱**: WebSocket 无认证、XSS 防护缺失、Token 存储不安全
6. **安全 P1 零实现**: 密码强度、登录限流、日志脱敏等 6 项均未落地
7. **测试覆盖不足**: 无并发测试、边界测试，测试报告已过时

### 🟢 长期改善（持续推进）
8. **文档治理**: PRD 版本冗余、任务分解过时、缺少运维文档
9. **架构优化**: Service 层实际未启用、WebSocket 广播改定向、延迟队列替代轮询

建议按 **Phase 1 → Phase 2 → Phase 3** 的顺序推进优化，优先解决金融安全、P0 功能缺失和前后端交付脱节问题。
