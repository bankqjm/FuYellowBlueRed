# FuYellowBlueRed 外卖平台 — 产品需求文档 (PRD)

> 版本: v2.0 | 更新日期: 2026-05-15 | 状态: 已评审

---

## 一、项目概述

### 1.1 项目背景
FuYellowBlueRed 是一个开源外卖配送平台，支持消费者、商家、骑手、管理员四种角色。当前已完成 MVP 核心业务闭环（注册登录→浏览商家→加购→下单→支付→配送→评价），并完成了 H5 移动端基础适配。现需对照美团外卖等业界标杆，进行产品体验升级和功能完善。

### 1.2 现有系统技术栈
- **前端**: React 18 + TypeScript + Ant Design 5 + Vite + Zustand
- **后端**: FastAPI + SQLAlchemy (async) + SQLite + JWT
- **API**: 56个端点，12个数据模型，6个Schema文件

### 1.3 后端API现状
- 56个API端点已实现
- **2个端点前端未调用**: `POST /upload`（文件上传）、`GET /shop/categories`（全部分类列表）
- **关键缺失**: 用户取消订单、商家拒绝订单原因、骑手完成配送确认、图片上传

---

## 二、需求清单

### 2.1 消费者端（USER）

#### P0 — 核心体验缺失

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| U-P0-01 | 用户取消订单 | 待支付/待接单状态可取消，已取消订单显示"再来一单" | 需新增API `PUT /orders/{id}/cancel` | Orders.tsx 增加取消按钮 |
| U-P0-02 | 支付倒计时 | 待支付订单显示15分钟倒计时，超时自动取消 | 需新增定时任务或前端倒计时 | Orders.tsx 增加倒计时组件 |
| U-P0-03 | 图片上传功能 | 头像、评价图片可上传 | 已有 `POST /upload` API，前端未对接 | 新增 uploadService，Profile/Review 页面集成 |
| U-P0-04 | 商家详情页数据真实化 | 月售/起送/配送费/配送时长/满减标签从后端获取 | 需扩展 Shop 模型增加 monthly_sales/min_order_amount/delivery_fee/delivery_time/discounts 字段 | ShopDetail.tsx 移除硬编码数据 |
| U-P0-05 | 购物车清空功能 | 可清空某店铺购物车 | 已有 `DELETE /orders/cart/shop/{shop_id}` | Cart.tsx 增加清空按钮 |
| U-P0-06 | 订单状态实时更新 | 订单列表页实时刷新状态变化 | 已有轮询机制，需优化 | Orders.tsx 优化轮询逻辑 |

#### P1 — 体验提升

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| U-P1-01 | 用户资料编辑 | 可修改昵称、头像 | 已有 `PUT /users/me` + `POST /upload` | Profile.tsx 增加编辑弹窗 |
| U-P1-02 | 收货地址管理完善 | 地址列表支持增删改查、设默认 | 已有完整CRUD API | Addresses.tsx 功能完善 |
| U-P1-03 | 订单详情页完善 | 显示完整商品明细、地址、状态时间线 | 已有 `GET /orders/{id}` | 优化 Orders.tsx 详情弹窗 |
| U-P1-04 | 评价功能完善 | 评价支持图片上传、骑手评分 | 已有 ReviewCreate schema | Review.tsx 增加图片上传和骑手评分 |
| U-P1-05 | 首页商家数据真实化 | 金刚区分类点击可筛选、Banner可配置 | 需后端增加分类筛选参数 | Home.tsx 对接真实筛选API |
| U-P1-06 | 搜索功能增强 | 搜索结果高亮、搜索历史 | 已有 keyword 参数 | Home.tsx 增加搜索历史组件 |

#### P2 — 体验打磨

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| U-P2-01 | 我的收藏 | 可收藏/取消收藏商家 | 需新增 Favorite 模型和API | 新增收藏功能 |
| U-P2-02 | 优惠券系统 | 商家可发券，用户可领券用券 | 需新增 Coupon 模型和API | 新增优惠券模块 |
| U-P2-03 | 钱包功能 | 余额查看、充值、支付 | 已有 Wallet 模型 | 新增钱包页面 |
| U-P2-04 | 客服中心 | 在线客服或FAQ | 需新增或接入第三方 | 新增客服页面 |
| U-P2-05 | 加购动效 | 加入购物车飞入动画 | 无需后端 | CSS动画 |
| U-P2-06 | 暗色模式 | 支持亮/暗主题切换 | 无需后端 | CSS变量体系改造 |

### 2.2 商家端（SHOP_OWNER）

#### P0 — 核心功能缺失

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| S-P0-01 | 商家数据看板 | 首页显示今日订单数/收入/评分/待处理 | 需新增 `GET /shop/my/stats` API | 新增 shop/Dashboard.tsx |
| S-P0-02 | 订单详情查看 | 可查看订单商品明细、地址、联系方式 | 已有 `GET /shop/my/orders/{id}` | shop/Orders.tsx 增加详情弹窗 |
| S-P0-03 | 商品图片上传 | 新增/编辑商品时可上传图片 | 已有 `POST /upload` | shop/Products.tsx 集成上传 |

#### P1 — 体验提升

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| S-P1-01 | 店铺信息编辑 | 可修改店铺名称/Logo/公告/营业时间 | 已有 `PUT /shop/my` | shop/ShopInfo.tsx 完善编辑功能 |
| S-P1-02 | 拒绝订单需填原因 | 拒绝订单时必须填写原因 | 需扩展 reject API 增加reason参数 | shop/Orders.tsx 增加原因输入 |
| S-P1-03 | 订单通知提醒 | 新订单到达时声音/震动提醒 | 需WebSocket或轮询 | 新增通知组件 |

### 2.3 骑手端（RIDER）

#### P0 — 核心功能缺失

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| R-P0-01 | 完成配送确认 | 骑手送达后确认完成 | 需新增 `PUT /rider/orders/{id}/complete` API | rider/Orders.tsx 增加完成按钮 |
| R-P0-02 | 提现功能完善 | 提现页面可输入金额和账户信息 | 已有 `POST /rider/withdraw` | rider/Withdraw.tsx 完善表单 |

#### P1 — 体验提升

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| R-P1-01 | 订单详情查看 | 可查看配送地址、联系方式 | 已有 `GET /orders/{id}` | rider/Orders.tsx 增加详情 |
| R-P1-02 | 一键联系用户 | 点击电话号码直接拨打 | 无需后端 | rider/Orders.tsx 增加 tel: 链接 |
| R-P1-03 | 骑手数据看板 | 今日接单数/收入/在线时长 | 需新增 `GET /rider/stats` API | rider 首页增加统计 |

### 2.4 管理端（ADMIN）

#### P1 — 体验提升

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| A-P1-01 | 数据看板增强 | 订单趋势图、收入趋势图 | 需扩展 `/admin/stats` 增加趋势数据 | admin/Dashboard.tsx 增加图表 |
| A-P1-02 | 店铺管理完善 | 可查看所有店铺（不仅待审核） | 需扩展 `/admin/shop/pending` 支持status筛选 | admin/Shops.tsx 增加筛选 |
| A-P1-03 | 订单管理 | 可查看所有订单、处理投诉 | 需新增 `/admin/orders` API | 新增 admin/Orders.tsx |

### 2.5 公共模块

#### P0 — 必须实现

| 需求ID | 需求描述 | 验收标准 | 后端支持 | 前端变更 |
|--------|---------|---------|---------|---------|
| C-P0-01 | 图片上传服务 | 前端统一调用上传API | 已有 `POST /upload` | 新增 services/upload.ts |
| C-P0-02 | Shop模型扩展 | 增加 monthly_sales/min_order_amount/delivery_fee/delivery_time/discounts | 需修改后端模型和Schema | 前端对接新字段 |
| C-P0-03 | 订单取消API | 用户可取消待支付/待接单订单 | 需新增后端API | 前端增加取消操作 |
| C-P0-04 | 骑手完成配送API | 骑手确认送达 | 需新增后端API | 前端增加完成操作 |

---

## 三、开发和测试计划

### 3.1 Sprint 1 — P0 核心功能（预计5天）

#### Day 1-2: 后端API扩展

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| Shop模型扩展: 增加 monthly_sales/min_order_amount/delivery_fee/delivery_time/discounts 字段 | models.py, schemas/shop.py, api/v1/shop.py | 2h |
| 新增用户取消订单API: `PUT /orders/{id}/cancel` | api/v1/orders.py, schemas/order.py | 1h |
| 新增骑手完成配送API: `PUT /rider/orders/{id}/complete` | api/v1/rider.py | 1h |
| 新增商家统计API: `GET /shop/my/stats` | api/v1/shop.py | 1h |
| 修复上传API: 确认 `POST /upload` 可正常工作 | api/v1/upload.py | 0.5h |
| 数据库迁移: 同步新字段 | Alembic或手动 | 0.5h |

#### Day 2-3: 前端P0功能开发

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| 新增上传服务 services/upload.ts | 新文件 | 0.5h |
| 用户取消订单功能 | Orders.tsx | 1h |
| 支付倒计时组件 | Orders.tsx | 1h |
| 图片上传集成（头像+评价） | Profile.tsx, Review.tsx | 1.5h |
| 商家详情页数据真实化 | ShopDetail.tsx, Home.tsx | 1h |
| 购物车清空功能 | Cart.tsx | 0.5h |
| 商家数据看板 | 新增 shop/Dashboard.tsx | 1.5h |
| 商家订单详情弹窗 | shop/Orders.tsx | 1h |
| 商家商品图片上传 | shop/Products.tsx | 0.5h |
| 骑手完成配送确认 | rider/Orders.tsx | 0.5h |
| 骑手提现功能完善 | rider/Withdraw.tsx | 1h |

#### Day 4-5: 集成测试与修复

| 测试项 | 测试方法 | 预计工时 |
|--------|---------|---------|
| 用户注册登录流程 | 手动测试 | 0.5h |
| 浏览→加购→下单→支付→取消 全流程 | 手动测试 | 1h |
| 商家接单→备餐→骑手取餐→配送→完成 全流程 | 手动测试 | 1h |
| 图片上传（头像/商品/评价） | 手动测试 | 0.5h |
| 移动端适配验证 | Chrome DevTools 模拟 | 1h |
| 四种角色切换测试 | 多账号测试 | 0.5h |
| TypeScript编译 + Vite构建 | 自动化 | 0.5h |
| Bug修复 | — | 2h |

### 3.2 Sprint 2 — P1 体验提升（预计4天）

#### Day 1-2: 后端+前端开发

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| 用户资料编辑弹窗 | Profile.tsx | 1h |
| 收货地址管理完善 | Addresses.tsx | 1.5h |
| 评价功能完善（图片+骑手评分） | Review.tsx | 1h |
| 商家店铺信息编辑 | shop/ShopInfo.tsx | 1h |
| 商家拒绝订单填原因 | shop/Orders.tsx | 0.5h |
| 骑手订单详情+联系用户 | rider/Orders.tsx | 1h |
| 骑手数据看板 | rider 首页 | 1h |
| 管理端数据看板增强 | admin/Dashboard.tsx | 1h |
| 管理端店铺管理完善 | admin/Shops.tsx | 0.5h |

#### Day 3-4: 测试与修复

| 测试项 | 测试方法 | 预计工时 |
|--------|---------|---------|
| 资料编辑+头像上传 | 手动测试 | 0.5h |
| 地址CRUD全流程 | 手动测试 | 0.5h |
| 评价+图片上传 | 手动测试 | 0.5h |
| 商家端全流程 | 手动测试 | 1h |
| 骑手端全流程 | 手动测试 | 1h |
| 管理端全流程 | 手动测试 | 0.5h |
| Bug修复 | — | 2h |

### 3.3 Sprint 3 — P2 体验打磨（预计3天，可按需排期）

| 任务 | 优先级 | 预计工时 |
|------|--------|---------|
| 收藏功能（需后端新增模型） | 中 | 3h |
| 优惠券系统（需后端新增模型） | 中 | 5h |
| 钱包功能（后端已有Wallet模型） | 中 | 2h |
| 加购动效 | 低 | 1h |
| 暗色模式 | 低 | 3h |
| 客服中心（FAQ页面） | 低 | 2h |

---

## 四、验收标准

### 4.1 功能验收
- [ ] 消费者可完成：注册→登录→浏览→搜索→加购→下单→支付→取消→评价 全流程
- [ ] 商家可完成：申请→审核→管理商品→接单→备餐→查看统计 全流程
- [ ] 骑手可完成：接单→取餐→配送→完成→查看收入→提现 全流程
- [ ] 管理员可完成：查看统计→审核店铺→管理用户 全流程
- [ ] 图片上传功能在所有入口正常工作
- [ ] 移动端所有页面正常显示和交互

### 4.2 质量验收
- [ ] TypeScript 编译 0 错误
- [ ] Vite 生产构建成功
- [ ] 无 console.error 或未捕获异常
- [ ] 移动端首屏加载 < 2秒

---

## 六、三方账务系统需求（账务管理专家视角）

### 6.1 账务系统概述

作为一个完整的外卖配送平台，需要实现标准的三方账务体系，确保资金流转透明、合规、可追溯。

**账务系统的核心目标**：
1. **资金安全**：所有资金变动必须有据可查，支持对账
2. **分账合规**：订单金额按规则分给平台、商家、骑手
3. **支付便捷**：支持支付宝、微信等多种支付方式
4. **结算高效**：商家和骑手的收入可快速提现到账
5. **风控完善**：防超付、防重复支付、防薅羊毛

### 6.2 资金流向设计

#### 订单资金流向图

```
┌─────────────────────────────────────────────────────────────────┐
│                        订单金额构成                               │
│                                                                 │
│   用户支付 ¥100.00                                              │
│   ├── 商品金额 ¥85.00                                          │
│   │   ├── 商家实收 ¥76.50 (90% 抽成10%)                        │
│   │   └── 平台抽成 ¥8.50                                       │
│   └── 配送费 ¥15.00                                            │
│       ├── 骑手收入 ¥12.00 (80%)                                 │
│       └── 平台服务费 ¥3.00 (20%)                                │
└─────────────────────────────────────────────────────────────────┘
```

**分账规则（可配置）**：
| 角色 | 收入来源 | 默认结算比例 | 平台抽成 | 提现规则 |
|------|---------|-------------|---------|---------|
| 商家 | 商品金额 | 90%（可配置） | 10%（可配置） | T+7结算 |
| 骑手 | 配送费 | 80%（可配置） | 20%（可配置） | 实时到账可提现 |
| 平台 | 商家抽成 + 骑手服务费 | 100%归平台 | — | — |

### 6.3 账务数据模型设计

#### 新增模型清单

| 模型名 | 表名 | 用途 |
|--------|------|------|
| `PaymentTransaction` | payment_transactions | 支付流水表，记录所有支付操作 |
| `ShopEarning` | shop_earnings | 商家收入表，记录商家每笔收入 |
| `PlatformCommission` | platform_commissions | 平台抽成记录表 |
| `FundFlow` | fund_flows | 资金流水表，记录所有账户余额变动 |
| `RefundRecord` | refund_records | 退款记录表 |

#### PaymentTransaction（支付流水表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 关联订单ID |
| user_id | Integer | 支付用户ID |
| trade_no | String(64) | 第三方交易流水号 |
| trade_type | String(20) | 交易类型：PAY/REFUND |
| amount | Float | 交易金额 |
| channel | String(20) | 支付渠道：ALIPAY/WECHAT/BALANCE |
| status | String(20) | 状态：PENDING/SUCCESS/FAILED/CLOSED |
| extra_data | Text | 扩展数据（JSON） |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间 |

#### ShopEarning（商家收入表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| shop_id | Integer | 商家ID |
| order_id | Integer | 关联订单ID |
| order_no | String(32) | 订单编号 |
| goods_amount | Float | 商品金额 |
| commission_rate | Float | 抽成比例（默认0.10） |
| commission_amount | Float | 抽成金额 |
| net_amount | Float | 商家实收金额 |
| status | String(20) | 状态：SETTLED（已结算）/UNSETTLED（未结算）/WITHDRAWN（已提现） |
| settled_at | DateTime | 结算时间 |
| created_at | DateTime | 创建时间 |

#### PlatformCommission（平台抽成记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 关联订单ID |
| shop_commission | Float | 商家抽成金额 |
| rider_service_fee | Float | 骑手服务费 |
| total | Float | 平台总收入 |
| created_at | DateTime | 创建时间 |

#### FundFlow（资金流水表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID |
| account_type | String(20) | 账户类型：USER/SHOP/RIDER/PLATFORM |
| flow_type | String(20) | 流水类型：INCOME/EXPENSE/FREEZE/UNFREEZE |
| amount | Float | 金额 |
| balance_before | Float | 变动前余额 |
| balance_after | Float | 变动后余额 |
| business_type | String(20) | 业务类型：ORDER_PAY/COMMISSION/WITHDRAW/BONUS |
| related_id | Integer | 关联业务ID（如订单ID、提现ID） |
| description | String(255) | 描述 |
| created_at | DateTime | 创建时间 |

#### RefundRecord（退款记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 关联订单ID |
| user_id | Integer | 退款用户ID |
| transaction_id | Integer | 原支付流水ID |
| refund_amount | Float | 退款金额 |
| refund_type | String(20) | 退款类型：AUTO_REFUND（超时）/MANUAL（手动取消） |
| status | String(20) | 状态：PENDING/PROCESSING/SUCCESS/FAILED |
| reason | String(255) | 退款原因 |
| processed_at | DateTime | 处理时间 |
| created_at | DateTime | 创建时间 |

### 6.4 可配置账务参数

#### 平台配置模型 (PlatformConfig)

| 配置项 | Key | 默认值 | 说明 |
|--------|-----|--------|------|
| 商家抽成比例 | SHOP_COMMISSION_RATE | 0.10 | 商品金额中平台抽成比例 |
| 骑手服务费比例 | RIDER_SERVICE_FEE_RATE | 0.20 | 配送费中平台收取的服务费比例 |
| 最低提现金额 | MIN_WITHDRAWAL_AMOUNT | 10.0 | 用户发起提现的最低金额限制 |
| 平台名称 | PLATFORM_NAME | FuYellowBlueRed | 平台显示名称 |
| 平台联系方式 | PLATFORM_CONTACT | 400-888-8888 | 平台客服电话 |

#### 配置管理API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取所有配置 | GET | /admin/config | 获取平台所有配置项 |
| 获取单个配置 | GET | /admin/config/{key} | 获取指定配置项 |
| 更新配置 | PUT | /admin/config/{key} | 更新指定配置项 |

**配置变更影响**：
- `SHOP_COMMISSION_RATE` 变更后，新订单按新比例计算商家收入
- `RIDER_SERVICE_FEE_RATE` 变更后，新订单按新比例计算骑手收入
- `MIN_WITHDRAWAL_AMOUNT` 变更后，影响提现校验规则

### 6.5 账务API设计

#### 用户端账务API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 支付订单 | POST | /orders/{id}/pay | 包含支付方式选择和钱包扣款 |
| 取消订单退款 | PUT | /orders/{id}/cancel | 包含退款逻辑 |
| 我的钱包 | GET | /wallet | 获取用户钱包余额 |
| 钱包充值 | POST | /wallet/recharge | 充值到钱包余额 |
| 支付流水 | GET | /wallet/transactions | 获取支付流水记录 |

#### 商家端账务API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 商家收入汇总 | GET | /shop/my/earnings/summary | 今日/本周/本月/总收入 |
| 商家收入明细 | GET | /shop/my/earnings | 收入流水列表 |
| 商家结算记录 | GET | /shop/my/settlements | 结算记录列表 |
| 商家提现 | POST | /shop/my/withdraw | 商家提现申请 |

#### 骑手端账务API（已有，需完善）

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 骑手收入汇总 | GET | /rider/earnings/summary | 今日/本周/本月/总收入 |
| 骑手收入明细 | GET | /rider/earnings | 收入流水列表 |
| 骑手提现 | POST | /rider/withdraw | 完善：支持多种账户类型 |

#### 管理端账务API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 平台账务概览 | GET | /admin/finance/overview | 总收入/总支出/总提现 |
| 商家结算管理 | GET | /admin/finance/shop-settlements | 商家结算列表 |
| 商家结算确认 | PUT | /admin/finance/shop-settlements/{id}/settle | 确认结算 |
| 骑手提现审核 | GET | /admin/finance/rider-withdrawals | 骑手提现列表 |
| 骑手提现审核 | PUT | /admin/finance/rider-withdrawals/{id}/approve | 审核提现 |
| 账务对账 | GET | /admin/finance/reconciliation | 日/周/月对账单 |
| 退款管理 | GET | /admin/finance/refunds | 退款列表 |
| 退款处理 | PUT | /admin/finance/refunds/{id}/process | 处理退款 |

### 6.6 账务需求清单

#### P0 — 核心账务功能（必须实现）

| 需求ID | 需求描述 | 验收标准 | 后端变更 | 前端变更 |
|--------|---------|---------|---------|---------|
| F-P0-01 | 用户钱包余额支付 | 下单时支持使用钱包余额支付，支付前校验余额 | 新增钱包扣款逻辑、FundFlow记录 | Cart.tsx 增加钱包支付选项 |
| F-P0-02 | 支付流水记录 | 每笔支付/退款必须记录到PaymentTransaction | 新增PaymentTransaction模型和API | 新增支付记录页面 |
| F-P0-03 | 商家收入计算 | 订单完成后计算商家实收金额，记录到ShopEarning | 新增ShopEarning模型和计算逻辑 | shop/Earnings.tsx 收入明细 |
| F-P0-04 | 骑手收入计算 | 配送完成后计算骑手收入，记录到RiderEarning | 修改deliver_order增加收入记录 | rider/Earnings.tsx |
| F-P0-05 | 资金流水记录 | 所有账户余额变动必须记录到FundFlow | 新增FundFlow模型 | 钱包页面显示资金流水 |
| F-P0-06 | 订单退款逻辑 | 用户取消已支付订单时，退款到钱包余额 | 新增RefundRecord模型和退款逻辑 | Orders.tsx 取消按钮增加退款提示 |
| F-P0-07 | 平台抽成记录 | 订单完成后记录平台抽成金额 | 新增PlatformCommission模型 | — |
| F-P0-08 | 账务参数可配置 | 商家抽成比例、骑手服务费比例等参数可通过后台配置 | 新增PlatformConfig模型和配置API | — |

#### P1 — 账务体验提升

| 需求ID | 需求描述 | 验收标准 | 后端变更 | 前端变更 |
|--------|---------|---------|---------|---------|
| F-P1-01 | 钱包充值功能 | 用户可充值到钱包余额（模拟） | 新增 wallet/recharge API | user/Wallet.tsx 充值页面 |
| F-P1-02 | 商家提现功能 | 商家可申请提现到银行账户 | 新增商家提现API和WithdrawalRecord | shop/Withdraw.tsx |
| F-P1-03 | 商家结算功能 | T+7自动结算商家收入 | 新增定时结算任务 | 商家提现页面 |
| F-P1-04 | 第三方支付对接 | 支持支付宝/微信支付（沙箱环境） | 新增第三方支付SDK集成 | Cart.tsx 增加支付方式选择 |
| F-P1-05 | 账务对账单 | 管理端可查看日/周/月账务对账单 | 新增对账API | admin/Finance.tsx |

#### P2 — 账务安全增强

| 需求ID | 需求描述 | 验收标准 | 后端变更 | 前端变更 |
|--------|---------|---------|---------|---------|
| F-P2-01 | 幂等性保证 | 支付/退款接口必须保证幂等，防止重复扣款 | 使用唯一流水号防重 | — |
| F-P2-02 | 事务一致性 | 钱包扣款和流水记录必须在同一事务 | 数据库事务管理 | — |
| F-P2-03 | 账务安全审计 | 记录关键操作的审计日志 | 新增审计日志表 | — |
| F-P2-04 | 账务异常告警 | 资金异常（超付、少付）自动告警 | 新增告警机制 | — |

### 6.7 账务开发计划

#### Sprint F1 — 核心账务（预计3天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | 设计并实现账务数据模型 | models.py 新增5个模型 |
| Day 1 | 实现用户钱包余额支付 | orders.py pay_order 修改 |
| Day 1 | 实现支付流水记录 | payment.py 新增API |
| Day 2 | 实现商家收入计算 | shop.py deliver_order 修改 |
| Day 2 | 实现资金流水记录 | fundflow.py 新增API |
| Day 2 | 实现骑手收入计算完善 | rider.py deliver_order 修改 |
| Day 3 | 实现订单退款逻辑 | orders.py cancel_order 修改 |
| Day 3 | 实现平台抽成记录 | commission.py 新增 |

#### Sprint F2 — 账务前端（预计2天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | 钱包页面重构 | user/Wallet.tsx 新增 |
| Day 1 | 支付页面增加支付方式 | Cart.tsx 修改 |
| Day 2 | 商家收入页面 | shop/Earnings.tsx 新增 |
| Day 2 | 骑手收入页面完善 | rider/Earnings.tsx 修改 |
| Day 2 | 订单页增加退款提示 | user/Orders.tsx 修改 |

#### Sprint F3 — 管理端账务（预计2天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | 管理端账务概览 | admin/Finance.tsx 新增 |
| Day 1 | 商家结算管理 | admin/ShopSettlements.tsx 新增 |
| Day 1 | 骑手提现审核 | admin/RiderWithdrawals.tsx 新增 |
| Day 2 | 账务对账单 | admin/Reconciliation.tsx 新增 |
| Day 2 | 退款管理 | admin/Refunds.tsx 新增 |

### 6.8 账务验收标准

#### 功能验收
- [ ] 用户下单可使用钱包余额支付
- [ ] 每笔支付生成唯一支付流水记录
- [ ] 订单完成后商家获得商品金额的90%
- [ ] 骑手完成配送后获得配送费的80%
- [ ] 所有账户余额变动有FundFlow记录
- [ ] 用户取消已支付订单可退款
- [ ] 管理端可查看完整账务数据

#### 安全验收
- [ ] 支付接口支持幂等（重复调用不重复扣款）
- [ ] 余额扣款和流水记录在同一事务
- [ ] 所有账务操作有审计日志

#### 对账验收
- [ ] 平台总收入 = 商家抽成 + 骑手服务费
- [ ] 用户支出 = 订单支付总额 - 退款总额
- [ ] 商家收入 = 订单商品总额 × 90%
- [ ] 骑手收入 = 订单配送费总额 × 80%

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| Shop模型扩展需数据库迁移 | 可能影响现有数据 | 新字段设默认值，不破坏现有数据 |
| 图片上传依赖文件系统存储 | 生产环境需对象存储 | 当前用本地存储，后续可切换S3 |
| 支付倒计时超时取消 | 需后端定时任务 | Sprint1先用前端倒计时+手动取消 |
| WebSocket实时通知 | 架构变更较大 | Sprint1用轮询替代，后续迭代加WS |

---

## 七、安全需求（安全专家视角）

### 7.1 安全概述

FuYellowBlueRed 作为一个涉及资金流转的外卖配送平台，安全性是核心需求。系统面临的主要安全威胁包括：

1. **资金安全威胁**：支付接口攻击、恶意充值、重复扣款
2. **身份认证威胁**：暴力破解、Token伪造、会话劫持
3. **数据安全威胁**：SQL注入、XSS攻击、敏感数据泄露
4. **文件安全威胁**：恶意文件上传 webshell

### 7.2 安全威胁建模

#### 资产识别
| 资产 | 分类 | 敏感性 |
|------|------|--------|
| 用户密码 | 认证凭证 | 高 |
| JWT Token | 会话凭证 | 高 |
| 钱包余额 | 金融资产 | 极高 |
| 支付流水 | 金融数据 | 极高 |
| 用户手机号 | 个人信息 | 中 |
| 商家银行账户 | 金融数据 | 高 |

#### 威胁场景
| 威胁 | 攻击方式 | 影响 | 可能性 |
|------|----------|------|--------|
| 恶意充值 | 绕过前端限制调用充值接口 | 资金损失 | 高 |
| 重复扣款 | 重复调用支付接口 | 用户资产损失 | 高 |
| 恶意文件 | 上传webshell | 服务器沦陷 | 中 |
| 暴力破解 | 大量尝试登录 | 账户被盗 | 高 |
| Token伪造 | 破解JWT密钥 | 身份冒充 | 低 |

### 7.3 安全需求清单

#### P0 — 必须实现

| 需求ID | 需求描述 | 验收标准 | 影响文件 |
|--------|---------|---------|---------|
| SEC-P0-01 | 支付接口幂等性保护 | 同一订单重复支付返回原结果，不重复扣款 | finance.py, orders.py |
| SEC-P0-02 | 充值/支付金额上限 | 单笔≤10,000元，每日≤50,000元 | wallet.py, finance.py |
| SEC-P0-03 | 文件上传类型白名单 | 仅允许 jpg/png/gif/webp，禁止 exe/php/py | upload.py |
| SEC-P0-04 | JWT密钥强制配置 | 生产环境必须通过环境变量配置 | config.py |
| SEC-P0-05 | 用户充值权限控制 | 移除用户自主充值，接入真实支付网关 | wallet.py |
| SEC-P0-06 | 账务事务一致性 | 余额扣减+流水记录原子操作 | finance.py, wallet.py |

#### P1 — 高优先级

| 需求ID | 需求描述 | 验收标准 | 影响文件 |
|--------|---------|---------|---------|
| SEC-P1-01 | 密码强度校验 | 至少8位，包含字母和数字 | auth.py |
| SEC-P1-02 | 登录失败限流 | 5次失败锁定15分钟 | auth.py |
| SEC-P1-03 | 敏感日志脱敏 | 日志不记录完整金额、密码等敏感信息 | 全局 |
| SEC-P1-04 | CORS严格配置 | 生产环境仅允许已知域名 | config.py, main.py |
| SEC-P1-05 | 错误信息保护 | 生产环境隐藏堆栈和内部错误 | main.py |
| SEC-P1-06 | 账户连续失败锁定 | 连续5次错误自动锁定 | auth.py |

#### P2 — 中优先级

| 需求ID | 需求描述 | 验收标准 | 影响文件 |
|--------|---------|---------|---------|
| SEC-P2-01 | Token安全存储 | 使用httpOnly Cookie或加密存储 | api.ts |
| SEC-P2-02 | 安全响应头 | 添加 X-Frame-Options, CSP 等 | main.py |
| SEC-P2-03 | 操作审计日志 | 关键操作完整记录 | models.py, 全局 |
| SEC-P2-04 | 速率限制 | 所有API接口限流 | main.py |
| SEC-P2-05 | 依赖安全扫描 | 定期扫描已知漏洞 | requirements.txt |
| SEC-P2-06 | 会话管理 | 登录设备管理、主动下线 | auth.py |

### 7.4 安全开发计划

#### Sprint Sec1 — 紧急修复（2天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | 支付幂等性保护 | finance.py, orders.py |
| Day 1 | 充值金额上限 | wallet.py |
| Day 1 | 文件类型白名单 | upload.py |
| Day 2 | JWT密钥强制检查 | config.py |
| Day 2 | 账务事务一致性 | finance.py |

#### Sprint Sec2 — 高优先级修复（3天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | 密码强度校验 | auth.py |
| Day 1 | 登录限流 | auth.py |
| Day 2 | 日志脱敏 | 全局 |
| Day 2 | CORS严格配置 | main.py |
| Day 3 | 账户锁定 | auth.py |

#### Sprint Sec3 — 中优先级（3天）

| Day | 任务 | 涉及文件 |
|-----|------|---------|
| Day 1 | Token安全存储 | api.ts |
| Day 1 | 安全响应头 | main.py |
| Day 2 | 审计日志系统 | models.py |
| Day 3 | 速率限制完善 | main.py |

### 7.5 安全验收标准

#### 功能验收
- [ ] 支付接口支持幂等（重复调用返回相同结果）
- [ ] 单笔充值上限 10,000 元
- [ ] 每日充值上限 50,000 元
- [ ] 仅支持图片文件上传（jpg/png/gif/webp）
- [ ] 生产环境 JWT 密钥必须通过环境变量配置
- [ ] 用户自主充值功能移除或管理员审批

#### 安全验收
- [ ] 密码强度校验生效（8位以上，含字母数字）
- [ ] 连续5次登录失败锁定15分钟
- [ ] 日志中不包含敏感信息（金额完整数据）
- [ ] CORS 仅允许指定域名
- [ ] 错误响应不包含堆栈信息

#### 安全测试
- [ ] SQL注入测试通过
- [ ] XSS攻击测试通过
- [ ] CSRF防护测试通过
- [ ] 暴力破解防护测试通过
- [ ] 文件上传绕过测试通过
