# FuYellowBlueRed 开发计划 v2.0

## 概述

本文档定义外卖平台项目的开发计划，包含 MVP 阶段（已完成）和 Phase 2 架构改进阶段。

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

### P4-P7 — 待开发

| 阶段 | 任务 | 优先级 |
|------|------|--------|
| P4 | API 版本控制 | P1 |
| P5 | 配置分层 | P1 |
| P6 | 前端 Hooks 抽取 | P1 |
| P7 | 前端组件拆分 | P1 |

**Service 层设计示例**:

```python
# app/services/order_service.py
class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, user_id: int, data: OrderCreate) -> Order:
        # 业务逻辑
        pass

    async def pay_order(self, order_id: int) -> Order:
        # 业务逻辑
        pass

    async def cancel_order(self, order_id: int, user_id: int) -> Order:
        # 业务逻辑
        pass

# app/api/orders.py - 重构后
@router.post("")
async def create_order(
    request: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.create_order(current_user.id, request)
    return ResponseSchema(code=0, data=OrderResponse.model_validate(order))
```

### P3 — 统一异常处理体系

**目标**: 建立统一的异常处理机制，统一错误响应格式

| 任务 | 状态 | 说明 |
|------|------|------|
| P3.1 | ⬜ | 创建 `app/core/exceptions.py` 异常类定义 |
| P3.2 | ⬜ | 创建 `app/core/handlers.py` 全局异常处理器 |
| P3.3 | ⬜ | 更新 `main.py` 注册异常处理器 |
| P3.4 | ⬜ | 统一所有 API 的错误响应格式 |
| P3.5 | ⬜ | 添加请求日志中间件 |

**异常类设计**:

```python
# app/core/exceptions.py
class BaseAPIException(Exception):
    status_code: int = 400
    message: str
    error_code: str

    def __init__(self, message: str = None):
        self.message = message or self.__class__.__doc__

class NotFoundException(BaseAPIException):
    status_code = 404
    error_code = "NOT_FOUND"

class UnauthorizedException(BaseAPIException):
    status_code = 401
    error_code = "UNAUTHORIZED"

class ForbiddenException(BaseAPIException):
    status_code = 403
    error_code = "FORBIDDEN"

class ValidationException(BaseAPIException):
    status_code = 422
    error_code = "VALIDATION_ERROR"

class BusinessException(BaseAPIException):
    status_code = 400
    error_code = "BUSINESS_ERROR"
```

### P4 — API 版本控制

**目标**: 添加 `/api/v1/` 版本前缀，便于未来 API 演进

| 任务 | 状态 | 说明 |
|------|------|------|
| P4.1 | ⬜ | 创建 `app/api/v1/` 目录 |
| P4.2 | ⬜ | 移动现有 API 到 v1 目录 |
| P4.3 | ⬜ | 创建 `app/api/v1/__init__.py` 统一导出 |
| P4.4 | ⬜ | 更新 `main.py` 路由注册 |
| P4.5 | ⬜ | 更新前端 API 调用路径 |

**目录结构**:

```
app/api/
├── __init__.py
├── deps.py              # 依赖注入
├── v1/
│   ├── __init__.py      # 统一导出
│   ├── auth.py
│   ├── users.py
│   ├── shops.py
│   ├── orders.py
│   ├── riders.py
│   ├── reviews.py
│   └── admin.py
└── v2/                  # 未来版本
    └── ...
```

### P5 — 配置分层

**目标**: 实现开发/生产环境配置分离

| 任务 | 状态 | 说明 |
|------|------|------|
| P5.1 | ⬜ | 创建 `app/core/config.py` 配置类 |
| P5.2 | ⬜ | 实现环境变量读取 |
| P5.3 | ⬜ | 创建 `.env.example` 示例文件 |
| P5.4 | ⬜ | 更新 `database.py` 使用配置类 |
| P5.5 | ⬜ | 添加 MySQL 配置支持 |
| P5.6 | ⬜ | 更新 Docker 配置 |

**配置类设计**:

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "FuYellowBlueRed"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./data.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
```

### P6 — 前端 Hooks 抽取

**目标**: 抽取自定义 Hooks，提高代码复用性

| 任务 | 状态 | 说明 |
|------|------|------|
| P6.1 | ⬜ | 创建 `src/hooks/` 目录 |
| P6.2 | ⬜ | 抽取 `useAuth.ts` 认证 Hook |
| P6.3 | ⬜ | 抽取 `useOrders.ts` 订单 Hook |
| P6.4 | ⬜ | 抽取 `useCart.ts` 购物车 Hook |
| P6.5 | ⬜ | 抽取 `useAddress.ts` 地址 Hook |
| P6.6 | ⬜ | 抽取 `useShops.ts` 商家 Hook |
| P6.7 | ⬜ | 重构页面组件使用 Hooks |
| P6.8 | ⬜ | 添加 Hooks 文档 |

**Hook 设计示例**:

```typescript
// src/hooks/useOrders.ts
import { useState, useEffect, useCallback } from 'react'
import { orderApi, OrderInfo } from '@/services/order'

export function useOrders(initialStatus?: string) {
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(initialStatus)

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true)
      const res = await orderApi.getOrders({ status })
      setOrders(res.data.items)
    } catch (error) {
      console.error('获取订单失败', error)
    } finally {
      setLoading(false)
    }
  }, [status])

  useEffect(() => {
    fetchOrders()
  }, [fetchOrders])

  return { orders, loading, status, setStatus, refetch: fetchOrders }
}
```

### P7 — 前端组件拆分

**目标**: 将大型页面组件拆分为更小的可复用组件

| 任务 | 状态 | 说明 |
|------|------|------|
| P7.1 | ⬜ | 创建 `src/components/` 目录 |
| P7.2 | ⬜ | 创建 `ErrorBoundary` 错误边界组件 |
| P7.3 | ⬜ | 创建 `Loading` 加载组件 |
| P7.4 | ⬜ | 拆分订单列表组件 |
| P7.5 | ⬜ | 拆分商品卡片组件 |
| P7.6 | ⬜ | 拆分地址选择组件 |
| P7.7 | ⬜ | 拆分评价组件 |

**组件结构示例**:

```
src/
├── components/
│   ├── ErrorBoundary/
│   │   ├── index.tsx
│   │   └── styles.ts
│   ├── Loading/
│   │   ├── index.tsx
│   │   └── styles.ts
│   ├── OrderList/
│   │   ├── index.tsx
│   │   ├── OrderItem.tsx
│   │   └── styles.ts
│   └── ProductCard/
│       ├── index.tsx
│       └── styles.ts
└── pages/
    └── user/
        └── Orders/
            ├── index.tsx    # 主组件（简洁）
            ├── OrderList.tsx  # 导入拆分的组件
            └── OrderDetail.tsx
```

### P8 — 数据库优化

**目标**: 添加索引优化查询性能

| 任务 | 状态 | 说明 |
|------|------|------|
| P8.1 | ⬜ | 分析查询热点 |
| P8.2 | ⬜ | 创建 Alembic 迁移添加索引 |
| P8.3 | ⬜ | 添加 orders 表索引 |
| P8.4 | ⬜ | 添加 products 表索引 |
| P8.5 | ⬜ | 添加 reviews 表索引 |
| P8.6 | ⬜ | 添加 cart_items 表索引 |
| P8.7 | ⬜ | 验证索引效果 |

**索引迁移示例**:

```python
# alembic/versions/add_indexes.py
def upgrade():
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    op.create_index('idx_products_shop_id', 'products', ['shop_id'])
    op.create_index('idx_reviews_shop_id', 'reviews', ['shop_id'])

def downgrade():
    op.drop_index('idx_orders_user_id')
    op.drop_index('idx_orders_status')
    # ...
```

### P9 — 日志审计系统

**目标**: 添加结构化日志记录关键操作

| 任务 | 状态 | 说明 |
|------|------|------|
| P9.1 | ⬜ | 创建 `app/core/logger.py` 日志配置 |
| P9.2 | ⬜ | 添加请求日志中间件 |
| P9.3 | ⬜ | 记录登录登出日志 |
| P9.4 | ⬜ | 记录订单操作日志 |
| P9.5 | ⬜ | 记录管理员操作日志 |
| P9.6 | ⬜ | 添加日志格式化配置 |

### P10 — 安全性增强

**目标**: 加强系统安全性

| 任务 | 状态 | 说明 |
|------|------|------|
| P10.1 | ⬜ | 添加请求限流中间件 |
| P10.2 | ⬜ | 增强输入验证 |
| P10.3 | ⬜ | 优化 CORS 配置 |
| P10.4 | ⬜ | 添加敏感数据脱敏 |

---

## Phase 2 任务优先级

| 阶段 | 任务 | 优先级 | 工作量 |
|------|------|--------|--------|
| P2 | Service 层抽取 | P0 | 高 |
| P3 | 统一异常处理 | P0 | 中 |
| P4 | API 版本控制 | P1 | 中 |
| P5 | 配置分层 | P1 | 中 |
| P8 | 数据库优化 | P0 | 低 |
| P6 | 前端 Hooks 抽取 | P1 | 高 |
| P7 | 前端组件拆分 | P1 | 高 |
| P9 | 日志审计系统 | P1 | 中 |
| P10 | 安全性增强 | P1 | 中 |

---

## 开发流程

### Phase 2 开发顺序

1. **P3 — 统一异常处理** (前置依赖最少，可优先完成)
2. **P5 — 配置分层** (其他任务依赖配置)
3. **P4 — API 版本控制** (不影响现有功能)
4. **P8 — 数据库优化** (可并行执行)
5. **P2 — Service 层抽取** (核心重构，需要仔细测试)
6. **P6 — 前端 Hooks 抽取** (可并行执行)
7. **P7 — 前端组件拆分** (依赖 P6)
8. **P9 — 日志审计系统** (可并行执行)
9. **P10 — 安全性增强** (最后执行)

### 每日开发流程

1. 从待办列表选取任务
2. 创建功能分支
3. 实现功能
4. 添加单元测试
5. 提交代码
6. 更新本文档任务状态

---

## 验收标准

### Phase 2 验收清单

- [ ] 所有 API 通过 Service 层调用
- [ ] 异常响应格式统一
- [ ] API 路由使用 `/api/v1/` 前缀
- [ ] 支持环境变量配置
- [ ] 关键查询添加索引
- [ ] 前端使用自定义 Hooks
- [ ] 通用组件抽离到 components 目录
- [ ] 日志记录关键操作
- [ ] 请求限流生效
- [ ] 单元测试覆盖率 ≥ 60%

