# 外卖平台开源项目 — 需求规格说明书 v2.0

## 1. 项目概述

### 1.1 项目名称

FuYellowBlueRed — 开源外卖配送平台

### 1.2 项目愿景

构建一个功能完整、架构清晰、易于二次开发的开源外卖配送平台，覆盖从用户下单到骑手配送的完整订单闭环，为小型外卖团队、校园配送、社区团购等场景提供可落地的技术方案。

### 1.3 开源协议

MIT License

### 1.4 MVP 核心目标

MVP 阶段聚焦**核心订单闭环**：用户浏览商家 → 加购下单 → 商家接单 → 骑手配送 → 用户收货评价。所有非核心路径均采用简化方案，确保快速交付可运行的系统。

---

## 2. 用户角色

| 角色 | 说明 |
|------|------|
| 消费者（User） | 浏览商家、下单、支付、评价 |
| 商家（Shop Owner） | 管理店铺信息、商品、接单、查看订单 |
| 骑手（Rider） | 接单、取餐、配送、查看收入 |
| 管理员（Admin） | 审核商家、管理用户、查看平台数据 |

---

## 3. 功能需求

### 3.1 用户模块

#### 3.1.1 注册与登录

- 手机号 + 密码注册
- 手机号 + 密码登录
- JWT Token 鉴权
- 角色选择（消费者 / 商家 / 骑手），注册后可切换

#### 3.1.2 个人信息

- 修改昵称、头像
- 管理收货地址（增删改查，设默认地址）
- 查看我的订单

### 3.2 商家模块

#### 3.2.1 店铺管理

- 商家申请开店（提交店铺名称、地址、营业时间、公告）
- 管理员审核开店申请
- 编辑店铺信息（logo、公告、营业状态）
- 店铺营业 / 休息切换

#### 3.2.2 商品管理

- 商品分类管理（增删改排序）
- 商品管理（名称、图片、价格，原价、描述、库存、上架/下架）
- 商品按分类展示

#### 3.2.3 订单处理

- 查看待处理订单
- 接单 / 拒单
- 标记备餐完成（等待骑手取餐）
- 查看历史订单

### 3.3 消费者 — 下单模块（核心闭环）

#### 3.3.1 浏览与搜索

- 商家列表（按距离排序，MVP 阶段使用基础距离计算）
- 商家详情页（店铺信息 + 商品分类列表）
- 商品搜索（按名称模糊搜索）

#### 3.3.2 购物车

- 添加商品到购物车（指定商家）
- 修改数量、删除商品
- 清空购物车
- 购物车数据与服务端同步

#### 3.3.3 下单与支付

- 确认订单页（收货地址、商品明细、配送费、备注）
- 提交订单
- **模拟支付**：点击支付后直接标记为已支付，不接入真实支付网关
- 支付成功后订单状态流转至"待接单"

#### 3.3.4 订单跟踪

- 查看订单列表（按状态筛选）
- 订单详情页（状态时间线、商品明细、配送信息）
- **轮询方案**：前端定时轮询订单状态，MVP 不使用 WebSocket

#### 3.3.5 评价

- 订单完成后对商家评分（1-5 星）+ 文字评价
- 订单完成后对骑手评分（1-5 星）
- 商家详情页展示评价列表

### 3.4 骑手模块

#### 3.4.1 接单与配送

- 查看待接单订单列表（商家备餐完成的订单）
- 接单
- 标记取餐
- 标记送达
- 查看进行中订单

#### 3.4.2 收入管理

- 查看收入明细（每单配送费）
- 查看累计收入
- **模拟提现**：提交提现请求，后台直接标记为已到账

### 3.5 管理员模块

- 商家开店审核（通过 / 拒绝）
- 用户管理（查看列表、禁用 / 启用）
- 平台概览数据（订单量、用户数、商家数，MVP 阶段仅基础统计）

---

## 4. 订单状态流转

```
PENDING_PAYMENT → PAID → PENDING_ACCEPT → ACCEPTED → PREPARING → READY_FOR_PICKUP
    → RIDER_PICKED_UP → DELIVERING → DELIVERED → COMPLETED
```

| 状态 | 触发者 | 说明 |
|------|--------|------|
| PENDING_PAYMENT | 系统 | 订单创建，等待支付 |
| PAID | 消费者 | 模拟支付完成 |
| PENDING_ACCEPT | 系统 | 等待商家接单 |
| ACCEPTED | 商家 | 商家接单 |
| PREPARING | 商家 | 商家备餐中 |
| READY_FOR_PICKUP | 商家 | 备餐完成，等待骑手取餐 |
| RIDER_PICKED_UP | 骑手 | 骑手取餐 |
| DELIVERING | 骑手 | 配送中 |
| DELIVERED | 骑手 | 已送达 |
| COMPLETED | 消费者 | 确认收货并评价 |

异常流转：
- 商家拒单 → CANCELLED（退款至钱包余额）
- 消费者支付前取消 → CANCELLED

---

## 5. 简化策略（MVP 决策）

| 模块 | 完整方案 | MVP 简化方案 | 说明 |
|------|----------|-------------|------|
| 支付 | 接入微信/支付宝支付 | 模拟支付 | 点击支付直接成功，资金记录写入钱包余额 |
| 地图与导航 | 接入地图 SDK，实时导航 | 基础距离计算 | 使用 Haversine 公式计算两点间距离，用于配送费估算和商家排序 |
| 实时通信 | WebSocket 推送 | 前端轮询 | 前端每 5 秒轮询订单状态接口 |
| 部署 | 微服务 + K8s | 单机部署 | 单进程 + SQLite/MySQL，Docker 一键启动 |
| 通知 | 短信/推送通知 | 站内消息 | 仅平台内消息提醒，不发送外部通知 |
| 图片存储 | OSS/S3 | 本地文件存储 | 图片保存到服务器本地磁盘 |

---

## 6. 架构需求

### 6.1 后端架构

#### 6.1.1 分层架构

```
backend/app/
├── api/                    # API 路由层
│   ├── v1/               # API 版本控制
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── shops.py
│   │   ├── orders.py
│   │   ├── riders.py
│   │   ├── reviews.py
│   │   └── admin.py
│   └── deps.py          # 依赖注入
├── services/             # 业务逻辑层
│   ├── auth_service.py
│   ├── user_service.py
│   ├── order_service.py
│   └── ...
├── schemas/              # 数据模型层（Pydantic）
├── models/              # 数据库模型（SQLAlchemy）
├── core/                 # 核心配置
│   ├── config.py
│   ├── security.py
│   └── exceptions.py
└── main.py
```

#### 6.1.2 依赖注入

- 使用 FastAPI 依赖注入系统管理：
  - 数据库会话
  - 当前用户
  - 配置

#### 6.1.3 异常处理体系

```python
class BaseAPIException(Exception):
    status_code: int = 400
    message: str
    error_code: str

class NotFoundException(BaseAPIException):
    status_code = 404
    error_code = "NOT_FOUND"

class UnauthorizedException(BaseAPIException):
    status_code = 401
    error_code = "UNAUTHORIZED"

class ForbiddenException(BaseAPIException):
    status_code = 403
    error_code = "FORBIDDEN"
```

#### 6.1.4 配置分层

```python
# 开发环境
DATABASE_URL=sqlite:///./dev.db
DEBUG=True

# 生产环境
DATABASE_URL=mysql://user:pass@host/db
DEBUG=False
```

#### 6.1.5 API 版本控制

- 所有 API 添加版本前缀：`/api/v1/`
- 便于未来 API 演进

### 6.2 前端架构

#### 6.2.1 分层结构

```
frontend/src/
├── pages/               # 页面组件
│   ├── user/
│   │   ├── Home/
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   └── ...
├── components/          # 通用组件
│   ├── ErrorBoundary/
│   └── Loading/
├── hooks/              # 自定义 Hooks
│   ├── useOrders.ts
│   ├── useCart.ts
│   └── useAuth.ts
├── services/           # API 服务
├── stores/            # 状态管理
└── utils/             # 工具函数
```

#### 6.2.2 组件设计原则

- 单一职责：每个组件只负责一个功能
- 可复用性：通用组件抽离到 components 目录
- 可测试性：业务逻辑通过 hooks 隔离

### 6.3 数据库架构

#### 6.3.1 索引优化

| 表名 | 索引字段 | 用途 |
|------|----------|------|
| orders | user_id, status, created_at | 订单查询优化 |
| products | shop_id, category_id | 商品查询优化 |
| reviews | shop_id | 评价列表查询 |
| cart_items | user_id | 购物车查询 |

#### 6.3.2 软删除（可选）

- 关键数据支持软删除
- `deleted_at` 字段记录删除时间
- 查询时自动过滤已删除数据

---

## 7. 技术架构

### 7.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | React + Ant Design (AntD) | 基于 AntD Pro 脚手架，多角色统一入口 |
| 后端 | Python (FastAPI) | 异步高性能，自动生成 OpenAPI 文档 |
| 数据库 | MySQL / SQLite | 开发阶段可用 SQLite，生产推荐 MySQL |
| ORM | SQLAlchemy | Python 生态主流 ORM |
| 认证 | JWT (PyJWT) | 无状态 Token 鉴权 |
| 部署 | Docker + Docker Compose | 一键启动所有服务 |

### 7.2 项目结构（规划）

```
FuYellowBlueRed/
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 数据模型
│   │   ├── api/             # API 路由
│   │   │   ├── v1/          # API 版本
│   │   │   └── deps.py      # 依赖注入
│   │   ├── services/        # 业务逻辑层
│   │   └── utils/           # 工具函数
│   ├── alembic/             # 数据库迁移
│   ├── tests/               # 测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── services/        # API 调用
│   │   ├── stores/          # 状态管理
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── LICENSE
└── README.md
```

### 7.3 API 设计原则

- RESTful 风格
- 统一响应格式：`{ "code": 0, "message": "success", "data": {...} }`
- 分页格式：`{ "items": [...], "total": 100, "page": 1, "page_size": 20 }`
- 认证方式：`Authorization: Bearer <token>`
- FastAPI 自动生成 Swagger 文档（`/docs`）和 ReDoc（`/redoc`）

---

## 8. 数据模型

### 8.1 核心实体

```
users ──1:1── wallets
  │
  ├──1:N── shops ──1:N── categories ──1:N── products
  │
  ├──1:N── orders ──1:N── order_items
  │               ──1:1── reviews
  │               ──1:N── rider_earnings
  │
  └──1:N── withdrawal_records
```

### 8.2 主要字段

**users** — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| phone | VARCHAR(20) UNIQUE | 手机号 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(50) | 昵称 |
| avatar | VARCHAR(255) | 头像路径 |
| role | ENUM(USER, SHOP_OWNER, RIDER, ADMIN) | 角色 |
| status | TINYINT | 状态（1=正常, 0=禁用） |
| created_at / updated_at | DATETIME | 时间戳 |

**shops** — 店铺表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK | 所属商家 |
| name | VARCHAR(100) | 店铺名称 |
| logo | VARCHAR(255) | 店铺 Logo |
| address | VARCHAR(255) | 地址 |
| latitude / longitude | DECIMAL(10,7) | 经纬度 |
| business_hours | VARCHAR(100) | 营业时间 |
| notice | VARCHAR(500) | 店铺公告 |
| rating | DECIMAL(2,1) | 评分 |
| status | TINYINT | 状态（0=待审核, 1=营业, 2=休息, -1=拒绝） |
| created_at / updated_at | DATETIME | 时间戳 |

**products** — 商品表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| shop_id | BIGINT FK | 所属店铺 |
| category_id | BIGINT FK | 分类 |
| name | VARCHAR(100) | 商品名称 |
| image | VARCHAR(255) | 商品图片 |
| price | DECIMAL(10,2) | 售价 |
| original_price | DECIMAL(10,2) | 原价 |
| description | VARCHAR(500) | 描述 |
| stock | INT | 库存 |
| sales | INT | 销量 |
| status | TINYINT | 状态（1=上架, 0=下架） |
| created_at / updated_at | DATETIME | 时间戳 |

**orders** — 订单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| order_no | VARCHAR(32) UNIQUE | 订单号 |
| user_id | BIGINT FK | 下单用户 |
| shop_id | BIGINT FK | 店铺 |
| rider_id | BIGINT FK NULL | 骑手 |
| address | VARCHAR(255) | 收货地址 |
| latitude / longitude | DECIMAL(10,7) | 收货经纬度 |
| phone | VARCHAR(20) | 联系电话 |
| remark | VARCHAR(500) | 备注 |
| total_amount | DECIMAL(10,2) | 订单总额 |
| delivery_fee | DECIMAL(10,2) | 配送费 |
| status | VARCHAR(20) | 订单状态 |
| created_at / updated_at | DATETIME | 时间戳 |

**order_items** — 订单明细表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| order_id | BIGINT FK | 订单 |
| product_id | BIGINT FK | 商品 |
| product_name | VARCHAR(100) | 商品名称（快照） |
| product_image | VARCHAR(255) | 商品图片（快照） |
| price | DECIMAL(10,2) | 单价（快照） |
| quantity | INT | 数量 |

**reviews** — 评价表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| order_id | BIGINT FK UNIQUE | 订单 |
| user_id | BIGINT FK | 评价用户 |
| shop_id | BIGINT FK | 被评商家 |
| rider_id | BIGINT FK NULL | 被评骑手 |
| shop_rating | INT | 商家评分（1-5） |
| rider_rating | INT NULL | 骑手评分（1-5） |
| content | VARCHAR(500) | 评价内容 |
| images | VARCHAR(1000) | 评价图片（逗号分隔） |
| created_at | DATETIME | 创建时间 |

**wallets** — 钱包表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK UNIQUE | 用户 |
| balance | DECIMAL(10,2) | 可用余额 |
| frozen_balance | DECIMAL(10,2) | 冻结余额 |
| created_at / updated_at | DATETIME | 时间戳 |

**rider_earnings** — 骑手收入表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| rider_id | BIGINT FK | 骑手 |
| order_id | BIGINT FK | 订单 |
| amount | DECIMAL(10,2) | 收入金额 |
| type | VARCHAR(20) | 类型（DELIVERY_FEE / BONUS） |
| created_at | DATETIME | 创建时间 |

**withdrawal_records** — 提现记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK | 用户 |
| amount | DECIMAL(10,2) | 提现金额 |
| method | VARCHAR(20) | 提现方式 |
| account | VARCHAR(100) | 提现账号 |
| status | VARCHAR(20) | 状态（PENDING / APPROVED / REJECTED / COMPLETED） |
| created_at / updated_at | DATETIME | 时间戳 |

**categories** — 商品分类表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| shop_id | BIGINT FK | 所属店铺 |
| name | VARCHAR(50) | 分类名称 |
| sort_order | INT | 排序 |
| created_at | DATETIME | 创建时间 |

---

## 9. 配送费计算规则（MVP 简化）

- 基础配送费：3 元（3km 以内）
- 超出部分：每增加 1km 加收 1 元
- 距离计算：使用 Haversine 公式，基于商家与收货地址的经纬度
- 最低配送费：3 元
- 最大配送距离：10km（超出则不可配送）

---

## 10. 前端页面规划

### 10.1 消费者端

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录/注册 | /login | 手机号+密码 |
| 首页 | / | 商家列表、搜索 |
| 商家详情 | /shop/:id | 商品分类、加购 |
| 购物车 | /cart | 确认商品 |
| 确认订单 | /order/confirm | 地址、备注、支付 |
| 订单列表 | /orders | 按状态筛选 |
| 订单详情 | /order/:id | 状态时间线 |
| 收货地址管理 | /addresses | 增删改查 |
| 个人中心 | /profile | 个人信息 |

### 10.2 商家端

| 页面 | 路径 | 说明 |
|------|------|------|
| 店铺管理 | /shop/manage | 店铺信息编辑 |
| 商品管理 | /shop/products | 商品 CRUD |
| 分类管理 | /shop/categories | 分类 CRUD |
| 订单管理 | /shop/orders | 接单/备餐/完成 |
| 开店申请 | /shop/apply | 提交申请 |

### 10.3 骑手端

| 页面 | 路径 | 说明 |
|------|------|------|
| 待接单列表 | /rider/orders | 可接订单 |
| 进行中订单 | /rider/active | 取餐/配送 |
| 收入明细 | /rider/earnings | 收入记录 |
| 提现 | /rider/withdraw | 模拟提现 |

### 10.4 管理端

| 页面 | 路径 | 说明 |
|------|------|------|
| 仪表盘 | /admin/dashboard | 基础统计 |
| 商家审核 | /admin/shops | 审核列表 |
| 用户管理 | /admin/users | 用户列表 |

---

## 11. 非功能需求

| 项目 | MVP 目标 |
|------|----------|
| 性能 | 单机支持 100 并发用户 |
| 可用性 | 无高可用要求，单节点部署 |
| 安全 | 密码 bcrypt 哈希、JWT 鉴权、CORS 配置 |
| 可观测性 | 基础日志输出（stdout） |
| 国际化 | MVP 仅支持中文 |
| 测试 | 核心业务逻辑单元测试覆盖率 ≥ 60% |

---

## 12. 里程碑规划

| 阶段 | 内容 | 交付物 |
|------|------|--------|
| M1 — 基础框架 | 项目脚手架、数据库建表、认证体系、Docker 配置 | 可运行的空项目 + 登录注册 |
| M2 — 商家与商品 | 商家开店申请、审核、商品/分类 CRUD | 商家端核心功能 |
| M3 — 核心订单闭环 | 购物车、下单、模拟支付、订单状态流转 | 消费者下单到商家接单 |
| M4 — 骑手配送 | 骑手接单、取餐、送达、收入管理 | 完整订单闭环 |
| M5 — 评价与管理 | 评价系统、管理后台、基础统计 | 全角色功能闭环 |
| M6 — 打磨优化 | UI 优化、错误处理、文档完善 | 可发布版本 |

---

## 13. 架构改进需求（Phase 2）

> 以下为架构优化需求，将在 MVP 完成后实施

### 13.1 后端架构优化

| 需求 | 说明 | 优先级 |
|------|------|--------|
| Service 层抽取 | 将业务逻辑从 API 路由分离到独立 Service 层 | P0 |
| 统一异常处理 | 建立异常处理体系，统一错误响应格式 | P0 |
| API 版本控制 | `/api/v1/` 前缀，便于未来 API 演进 | P1 |
| 配置分层 | 开发/生产环境配置分离 | P1 |
| 日志审计 | 结构化日志记录关键操作 | P1 |

### 13.2 前端架构优化

| 需求 | 说明 | 优先级 |
|------|------|--------|
| Hooks 抽取 | 抽取 useOrders、useCart 等自定义 Hooks | P1 |
| 组件拆分 | 页面组件拆分为更小的可复用组件 | P1 |
| 错误边界 | 统一错误处理组件 | P2 |
| 加载骨架屏 | 提升首屏加载体验 | P2 |

### 13.3 数据库优化

| 需求 | 说明 | 优先级 |
|------|------|--------|
| 添加索引 | orders, products, reviews 表索引优化 | P0 |
| 连接池配置 | 数据库连接池大小配置 | P1 |
| 软删除预留 | deleted_at 字段预留 | P2 |

