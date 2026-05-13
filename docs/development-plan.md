# FuYellowBlueRed 开发计划 v2.0

## 概述

本文档定义外卖平台项目的开发计划，包含 MVP 阶段（已完成）和 Phase 2 架构改进阶段（已完成）。

---

## Phase 1: MVP 开发（已完成）

### M1 — 基础框架 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M1.1 | ✅ | FastAPI 项目结构、数据库连接 |
| M1.2 | ✅ | SQLAlchemy ORM 配置 |
| M1.3 | ✅ | 用户注册/登录 API |
| M1.4 | ✅ | JWT Token 认证 |
| M1.5 | ✅ | 统一响应格式封装 |
| M1.6 | ✅ | React + Vite 项目脚手架 |
| M1.7 | ✅ | 登录/注册页面 |
| M1.8 | ✅ | Ant Design + Zustand 集成 |
| M1.9 | ✅ | Docker Compose 配置 |

### M2 — 商家与商品 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M2.1 | ✅ | 店铺申请 API |
| M2.2 | ✅ | 店铺审核 API |
| M2.3 | ✅ | 商品分类 CRUD API |
| M2.4 | ✅ | 商品 CRUD API |
| M2.5 | ✅ | 商家店铺管理页面 |
| M2.6 | ✅ | 商品分类管理页面 |
| M2.7 | ✅ | 商品管理页面 |
| M2.8 | ✅ | 图片上传功能 |

### M3 — 核心订单闭环 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M3.1 | ✅ | 收货地址 API |
| M3.2 | ✅ | 购物车和订单 Schema |
| M3.3 | ✅ | 购物车 API |
| M3.4 | ✅ | 订单创建和支付 API |
| M3.5 | ✅ | 商家订单管理 API |
| M3.6 | ✅ | 用户端商家列表页面 |
| M3.7 | ✅ | 用户端商家详情页面 |
| M3.8 | ✅ | 购物车页面 |
| M3.9 | ✅ | 订单列表和支付页面 |
| M3.10 | ✅ | 商家订单管理页面 |
| M3.11 | ✅ | 地址管理页面 |

### M4 — 骑手配送 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M4.1 | ✅ | 骑手待接单列表 API |
| M4.2 | ✅ | 骑手接单 API |
| M4.3 | ✅ | 骑手取餐确认 API |
| M4.4 | ✅ | 骑手送达确认 API |
| M4.5 | ✅ | 骑手进行中订单 API |
| M4.6 | ✅ | 骑手收入明细 API |
| M4.7 | ✅ | 骑手累计收入 API |
| M4.8 | ✅ | 骑手模拟提现 API |
| M4.9 | ✅ | 订单状态轮询 API |
| M4.10 | ✅ | 骑手订单管理页面 |
| M4.11 | ✅ | 骑手收入页面 |
| M4.12 | ✅ | 骑手提现页面 |
| M4.13 | ✅ | 用户确认收货页面 |
| M4.14 | ✅ | 用户订单状态轮询 |

### M5 — 评价与管理 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M5.1 | ✅ | 提交评价 API |
| M5.2 | ✅ | 评价列表 API |
| M5.3 | ✅ | 更新商家评分 |
| M5.4 | ✅ | 管理员用户列表 API |
| M5.5 | ✅ | 管理员禁用/启用用户 API |
| M5.6 | ✅ | 管理员平台统计 API |
| M5.7 | ✅ | 用户评价页面 |
| M5.8 | ✅ | 管理员仪表盘 |
| M5.9 | ✅ | 管理员用户管理页面 |

### M6 — 打磨优化 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| M6.1 | ✅ | 全局错误处理 |
| M6.2 | ✅ | 输入校验完善 |
| M6.3 | ✅ | 响应式布局适配 |
| M6.4 | ✅ | 项目文档完善 |
| M6.5 | ✅ | 种子数据脚本 |

---

## Phase 2: 架构改进（已完成）

### P3 — 统一异常处理体系 ✅

**目标**: 建立统一的异常处理机制，统一错误响应格式

| 任务 | 状态 | 说明 |
|------|------|------|
| P3.1 | ✅ | 创建 `app/core/exceptions.py` 异常类定义 |
| P3.2 | ✅ | 创建日志系统 `app/core/logger.py` |
| P3.3 | ✅ | 创建请求日志中间件 `app/core/middleware.py` |
| P3.4 | ✅ | 更新 `main.py` 注册异常处理器 |
| P3.5 | ✅ | 统一所有 API 的错误响应格式 |

### P8 — 数据库索引优化 ✅

**目标**: 添加索引优化查询性能

| 任务 | 状态 | 说明 |
|------|------|------|
| P8.1 | ✅ | 添加 orders 表索引（user_id, shop_id, status, created_at） |
| P8.2 | ✅ | 添加 products 表索引（shop_id, category_id, status, name） |
| P8.3 | ✅ | 添加 reviews 表索引（shop_id, user_id, created_at） |
| P8.4 | ✅ | 添加 cart_items 表索引 |
| P8.5 | ✅ | 添加 rider_earnings, withdrawal_records 表索引 |

### P2 — Service 层抽取 ✅（基础）

**目标**: 将业务逻辑从 API 路由分离，提高代码可维护性和可测试性

| 任务 | 状态 | 说明 |
|------|------|------|
| P2.1 | ✅ | 创建 `app/services/` 目录结构 |
| P2.2 | ✅ | 创建 `base.py` 服务基类 |
| P2.3 | ✅ | 创建 `auth_service.py` 认证服务 |
| P2.4 | ✅ | 创建 `order_service.py` 订单服务 |

### P4 — API 版本控制 ✅

**目标**: 添加 `/api/v1/` 版本前缀，便于未来 API 演进

| 任务 | 状态 | 说明 |
|------|------|------|
| P4.1 | ✅ | 创建 `app/api/v1/` 目录 |
| P4.2 | ✅ | 移动现有 API 到 v1 目录 |
| P4.3 | ✅ | 创建 `app/api/v1/__init__.py` 统一导出 |
| P4.4 | ✅ | 更新 `main.py` 路由注册为 `/api/v1/` |
| P4.5 | ✅ | 更新前端 API 调用路径 |

### P5 — 配置分层 ✅

**目标**: 实现开发/生产环境配置分离

| 任务 | 状态 | 说明 |
|------|------|------|
| P5.1 | ✅ | 更新 `app/config.py` 配置类 |
| P5.2 | ✅ | 实现环境变量读取（.env） |
| P5.3 | ✅ | 创建 `.env.example` 示例文件 |
| P5.4 | ✅ | 添加 CORS_ORIGINS 解析属性 |
| P5.5 | ✅ | 更新 `main.py` 使用配置类 |

### P6 — 前端 Hooks 抽取 ✅

**目标**: 抽取自定义 Hooks，提高代码复用性

| 任务 | 状态 | 说明 |
|------|------|------|
| P6.1 | ✅ | 创建 `src/hooks/` 目录 |
| P6.2 | ✅ | 抽取 `useOrders.ts` 订单 Hook |
| P6.3 | ✅ | 抽取 `useCart.ts` 购物车 Hook |
| P6.4 | ✅ | 抽取 `useAddresses.ts` 地址 Hook |
| P6.5 | ✅ | 创建 `hooks/index.ts` 统一导出 |

### P7 — 前端组件拆分 ✅

**目标**: 将大型页面组件拆分为更小的可复用组件

| 任务 | 状态 | 说明 |
|------|------|------|
| P7.1 | ✅ | 创建 `src/components/` 目录 |
| P7.2 | ✅ | 创建 `ErrorBoundary` 错误边界组件 |
| P7.3 | ✅ | 创建 `Loading` 加载组件 |
| P7.4 | ✅ | 创建 `components/index.ts` 统一导出 |

---

## Phase 2 任务完成总结

### 后端改进
1. **统一异常处理**: 创建了完整的异常类体系，包括 NotFoundException、UnauthorizedException、ForbiddenException 等
2. **日志系统**: 实现了结构化日志和请求日志中间件
3. **数据库索引**: 为高频查询表添加了索引优化
4. **API 版本控制**: 引入 `/api/v1/` 前缀，便于未来 API 演进
5. **配置管理**: 支持 `.env` 文件配置，CORS 配置优化
6. **Service 层**: 创建了服务基类和基础服务（认证、订单）

### 前端改进
1. **自定义 Hooks**: 抽取了 useOrders、useCart、useAddresses 等 Hooks
2. **通用组件**: 创建了 ErrorBoundary、Loading 等可复用组件
3. **API 路径**: 统一更新为 `/api/v1/` 前缀

---

## 开发流程

### 已完成的工作流程
1. 从待办列表选取任务
2. 创建功能实现
3. 验证代码能正常工作
4. 更新开发计划文档任务状态

---

## 验收标准

### Phase 2 验收清单 ✅

- [x] 异常响应格式统一
- [x] API 路由使用 `/api/v1/` 前缀
- [x] 支持环境变量配置
- [x] 关键查询添加索引
- [x] 前端自定义 Hooks 已抽取
- [x] 通用组件抽离到 components 目录
- [x] 日志系统已实现

---

## 项目结构展示

### 后端项目结构
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── shop.py
│   │   │   ├── orders.py
│   │   │   ├── rider.py
│   │   │   ├── admin.py
│   │   │   ├── review.py
│   │   │   └── upload.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── logger.py
│   │   └── middleware.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── auth_service.py
│   │   └── order_service.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── .env.example
├── requirements.txt
└── scripts/
    └── seed_data.py
```

### 前端项目结构
```
frontend/
├── src/
│   ├── components/
│   │   ├── __init__.py (index.ts)
│   │   ├── ErrorBoundary.tsx
│   │   └── Loading.tsx
│   ├── hooks/
│   │   ├── index.ts
│   │   ├── useOrders.ts
│   │   ├── useCart.ts
│   │   └── useAddresses.ts
│   ├── services/
│   │   └── api.ts
│   └── pages/
```
