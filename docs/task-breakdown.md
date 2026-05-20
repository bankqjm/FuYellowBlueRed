# FuYellowBlueRed 开发任务拆解

## 开发目标

构建一个功能完整的外卖配送平台 MVP，采用 FastAPI + React + Ant Design 技术栈，覆盖消费者下单、商家接单、骑手配送的完整闭环。按 M1-M6 里程碑顺序开发，总计 103 项具体任务。

## 实现状态概览

| 维度 | 当前状态 | 说明 |
|------|----------|------|
| 后端 API | 61 个已实现 | 覆盖认证、用户、商家、商品、订单、骑手、钱包、优惠券、收藏、审核日志等模块 |
| 数据模型 | 18 个已实现 | User、Wallet、UserAddress、Favorite、Shop、Category、Product、Order、OrderItem、CartItem、Review、RiderEarning、WithdrawalRecord、PaymentTransaction、ShopEarning、PlatformCommission、FundFlow、RefundRecord、PlatformConfig、AuditLog、FinanceAuditLog、Coupon、UserCoupon |
| 前端页面 | 22 个已实现 | 登录/注册、用户首页/订单/钱包/地址/评价、商家仪表盘/订单/商品、骑手订单/收入/提现、管理员仪表盘/用户/商家/订单 |
| 测试覆盖 | 375 个测试用例 | 单元测试 + 集成测试 + 并发测试 + 边界测试 |

---

## 技术栈确认

| 层级 | 技术选型 | 版本要求 |
|------|----------|----------|
| 后端框架 | FastAPI | 0.109+ |
| Python | Python | 3.11+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| 数据库 | MySQL 8.0 / SQLite | — |
| 数据校验 | Pydantic | 2.0+ |
| 迁移工具 | Alembic | 1.13+ |
| 前端框架 | React 18 | 18.x |
| UI 库 | Ant Design | 5.x |
| 路由 | React Router | 6.x |
| 状态管理 | Zustand | 4.x |
| HTTP 客户端 | Axios | 1.x |
| 构建工具 | Vite | 5.x |

---

## 任务清单

### M1 — 基础框架搭建

#### 后端（12 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B1.1 | 初始化 FastAPI 项目 | 创建 `backend/` 目录结构，安装依赖（fastapi, uvicorn, sqlalchemy, alembic, pydantic, pydantic-settings, python-jose, passlib, bcrypt, aiosqlite, python-multipart），创建 `requirements.txt`，配置 pydantic-settings 环境变量管理 | — | 输出：`requirements.txt`、`.env.example` | 无 | P0 |
| B1.2 | 项目配置模块 | 创建 `app/config.py`（数据库 URL、CORS 域名、JWT 密钥等）、`app/__init__.py` | — | 输出：`app/config.py` | B1.1 | P0 |
| B1.3 | 数据库连接模块 | 创建 `app/database.py`，配置 async engine、async sessionmaker，支持 SQLite（开发）和 MySQL（生产）自动切换 | `.env` 数据库配置 | 输出：`app/database.py` | B1.1 | P0 |
| B1.4 | 所有数据模型 | 创建 `app/models/__init__.py`，定义 9 张表：User, Shop, Category, Product, Order, OrderItem, Review, Wallet, RiderEarning, WithdrawalRecord, UserAddress（收货地址） | 数据模型 ER 图 | 输出：`app/models/*.py` | B1.3 | P0 |
| B1.5 | Alembic 迁移配置 | 初始化 alembic（`alembic init alembic`），配置 `alembic.ini` 指向异步 engine，编写 `env.py` 加载配置，创建初始迁移脚本 | B1.4 定义好的模型 | 输出：`alembic/` 目录、初始迁移文件 | B1.4 | P0 |
| B1.6 | Pydantic Schema 层 | 创建 `app/schemas/__init__.py`，定义请求/响应模型：UserSchema, LoginRequest, RegisterRequest, TokenResponse, PageParams, PageResponse 等 | API 契约文档 | 输出：`app/schemas/*.py` | B1.4 | P0 |
| B1.7 | 统一响应工具 | 创建 `app/utils/response.py`，封装 `success()`, `error()`, `page_success()`，统一返回 `{code, message, data}` 格式 | — | 输出：`app/utils/response.py` | B1.6 | P0 |
| B1.8 | JWT 认证工具 | 创建 `app/utils/auth.py`，实现 `create_access_token()`, `verify_token()`，密码哈希 `hash_password()`, `verify_password()` | — | 输出：`app/utils/auth.py` | 无 | P0 |
| B1.9 | 认证依赖注入 | 创建 `app/deps/auth.py`，实现 `get_current_user()` 依赖，从 Authorization Header 解析 Token 并查询用户 | JWT Secret 配置 | 输出：`app/deps/auth.py` | B1.8 | P0 |
| B1.10 | 用户注册 API | POST `/api/auth/register`：校验手机号唯一 → bcrypt 哈希密码 → 创建 User + 自动创建 Wallet → 返回用户信息 | `RegisterRequest` | 输出：`app/api/auth.py` | B1.9 | P0 |
| B1.11 | 用户登录 API | POST `/api/auth/login`：校验手机号+密码 → 生成 JWT → 返回 Token + 用户信息 | `LoginRequest` | 输出：`app/api/auth.py` | B1.10 | P0 |
| B1.12 | 用户信息 API | GET `/api/users/me`：返回当前用户信息；PUT `/api/users/me`：更新昵称/头像 | Token（Header） | 输出：`app/api/users.py` | B1.10 | P0 |
| B1.13 | 文件上传 API | POST `/api/upload`：接收文件流，保存到 `uploads/` 目录，返回文件 URL（限制 5MB） | Multipart 文件 | 输出：`app/api/upload.py` | B1.1 | P1 |
| B1.14 | CORS 与安全中间件 | 在 `app/main.py` 中配置 CORSMiddleware（允许前端域名）、slowapi 限流（100次/分钟） | 前端端口配置 | 输出：`app/main.py` | B1.1 | P0 |
| B1.15 | 后端 Dockerfile | 创建 `backend/Dockerfile`：基于 python:3.11-slim，安装依赖，暴露 8000 端口 | `requirements.txt` | 输出：`backend/Dockerfile` | B1.1 | P1 |

#### 前端（8 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F1.1 | 初始化 React + Vite 项目 | 创建 `frontend/` 目录，使用 Vite 初始化 React 项目，安装依赖（antd, react-router-dom, axios, zustand, @ant-design/icons） | — | 输出：`frontend/` 脚手架 | 无 | P0 |
| F1.2 | Ant Design 主题配置 | 配置 `App.tsx`，引入 AntD ConfigProvider，设置中文语言包和主题色 | 品牌色配置 | 输出：`src/App.tsx` | F1.1 | P0 |
| F1.3 | 路由配置 | 创建 `src/router/index.tsx`，配置路由表：/login, /register, /user/*, /shop/*, /rider/*, /admin/*，创建基础 Layout 组件 | 页面清单（需求文档 9 节） | 输出：`src/router/` | F1.1 | P0 |
| F1.4 | Axios 封装 | 创建 `src/services/api.ts`：创建 axios 实例，配置 baseURL=环境变量，添加请求拦截器（注入 Authorization）、响应拦截器（401 跳转登录） | 后端 API 基础路径 | 输出：`src/services/api.ts` | F1.1 | P0 |
| F1.5 | 全局状态管理 | 创建 `src/stores/authStore.ts`（Zustand）：存储 userInfo, token, role，提供 login/logout/updateUser 方法，持久化到 localStorage | — | 输出：`src/stores/authStore.ts` | F1.4 | P0 |
| F1.6 | 登录页面 | 创建 `src/pages/Login/index.tsx`：手机号+密码表单，调用登录 API，成功后跳转首页 | UI 设计稿 | 输出：`src/pages/Login/` | F1.4, F1.5 | P0 |
| F1.7 | 注册页面 | 创建 `src/pages/Register/index.tsx`：手机号+密码+昵称+角色选择（USER/SHOP_OWNER/RIDER），调用注册 API | UI 设计稿 | 输出：`src/pages/Register/` | F1.4, F1.5 | P0 |
| F1.8 | 角色路由守卫 | 创建 `src/components/AuthGuard.tsx`：根据 token 和 role 控制页面访问，无权限重定向 | 角色权限表 | 输出：`src/components/AuthGuard.tsx` | F1.5 | P0 |
| F1.9 | 角色首页 | 创建消费者首页 `/user/home`、商家首页 `/shop/home`、骑手首页 `/rider/home`、管理员首页 `/admin/dashboard`（MVP 阶段可先用占位页面） | — | 输出：`src/pages/` 各角色首页 | F1.8 | P0 |
| F1.10 | Docker 配置 | 创建 `frontend/Dockerfile`：基于 node:18-alpine，构建生产镜像 | `package.json` | 输出：`frontend/Dockerfile` | F1.1 | P1 |

#### DevOps（2 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| D1.1 | docker-compose.yml | 创建项目根目录 `docker-compose.yml`：定义 backend、frontend、mysql（可选）服务，配置网络和卷挂载 | B1.15, F1.10 | 输出：`docker-compose.yml` | B1.15, F1.10 | P0 |
| D1.2 | 环境变量配置 | 创建 `.env.example`（后端）、`frontend/.env.example`（前端），说明各配置项含义 | — | 输出：`.env.example` 文件 | B1.1, F1.1 | P1 |

---

### M2 — 商家与商品

#### 后端（7 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B2.1 | 商家 Schema | 创建 `app/schemas/shop.py`, `app/schemas/product.py`, `app/schemas/category.py`：ShopCreate, ShopUpdate, ProductCreate, ProductUpdate, CategoryCreate 等 | API 契约 | 输出：`app/schemas/*.py` | M1 | P0 |
| B2.2 | 商家 CRUD API | POST `/api/shops`（商家提交申请，status=PENDING）|ShopCreate|输出：`app/api/shops.py`|M1|P0|
| B2.3 | 商家店铺 API | GET `/api/shops/my`：获取当前商家店铺；PUT `/api/shops/:id`：更新店铺信息、切换营业状态 | Token | 输出：`app/api/shops.py` | B2.2 | P0 |
| B2.4 | 管理员审核 API | PUT `/api/admin/shops/:id/review`：通过（status=APPROVED）或拒绝（status=REJECTED），附拒绝原因 | Token（ADMIN） | 输出：`app/api/admin.py` | B2.2 | P0 |
| B2.5 | 分类 CRUD API | GET/POST `/api/shops/:id/categories`（列表/新增）；PUT/DELETE `/api/shops/:id/categories/:cat_id`（更新/删除，含排序） | Token（SHOP_OWNER） | 输出：`app/api/categories.py` | B2.3 | P0 |
| B2.6 | 商品 CRUD API | GET/POST `/api/shops/:id/products`（列表/新增）；PUT/DELETE `/api/shops/:id/products/:prod_id`（更新/删除，含上下架） | Token（SHOP_OWNER） | 输出：`app/api/products.py` | B2.3 | P0 |
| B2.7 | 商家订单 API | GET `/api/shops/orders`：商家查看本店所有订单；PUT `/api/shops/orders/:id/status`：接单/拒单/备餐状态更新 | Token（SHOP_OWNER） | 输出：`app/api/shop_orders.py` | M1 | P0 |

#### 前端（5 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F2.1 | API 服务层 | 创建 `src/services/shop.ts`, `src/services/product.ts`：封装商家、商品、分类相关 API 调用 | B2.2-B2.7 | 输出：`src/services/*.ts` | M1 | P0 |
| F2.2 | 开店申请页面 | `/shop/apply`：表单组件（名称、地址、Logo上传、营业时间、公告），调用 POST /api/shops | UI 设计稿 | 输出：`src/pages/shop/Apply/` | F2.1 | P0 |
| F2.3 | 店铺管理页面 | `/shop/manage`：展示店铺信息卡片、编辑表单、营业/休息切换开关 | UI 设计稿 | 输出：`src/pages/shop/Manage/` | F2.1 | P0 |
| F2.4 | 分类管理页面 | `/shop/categories`：分类列表（拖拽排序）、新增/编辑弹窗、删除确认 | UI 设计稿 | 输出：`src/pages/shop/Categories/` | F2.1 | P0 |
| F2.5 | 商品管理页面 | `/shop/products`：商品列表（上下架筛选）、新增/编辑商品表单（含图片上传） | UI 设计稿 | 输出：`src/pages/shop/Products/` | F2.1 | P0 |
| F2.6 | 管理员商家审核页面 | `/admin/shops`：待审核列表、操作列（通过/拒绝按钮），调用审核 API | UI 设计稿 | 输出：`src/pages/admin/Shops/` | F2.1 | P0 |

---

### M3 — 核心订单闭环（消费者侧）

#### 后端（12 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B3.1 | 收货地址 Schema 与 API | 创建 `app/schemas/address.py`，实现 `/api/users/addresses` CRUD + 设置默认地址 | Token（USER） | 输出：`app/api/addresses.py` | M1 | P0 |
| B3.2 | Haversine 距离计算工具 | 创建 `app/utils/distance.py`：实现 Haversine 公式，输入两对经纬度返回公里数 | — | 输出：`app/utils/distance.py` | M1 | P0 |
| B3.3 | 配送费计算服务 | 创建 `app/services/delivery_fee.py`：基础 3 元（3km内），超出每 km +1 元，最大 10km | B3.2 | 输出：`app/services/delivery_fee.py` | B3.2 | P0 |
| B3.4 | 商家列表 API | GET `/api/shops/list`：返回审核通过的营业中商家列表，含距离字段（根据用户经纬度计算）| 用户经纬度 | 输出：`app/api/shops.py` | B3.2 | P0 |
| B3.5 | 商家详情 API | GET `/api/shops/:id`：返回商家信息 + 分类列表（含商品列表） | — | 输出：`app/api/shops.py` | B3.4 | P0 |
| B3.6 | 商品搜索 API | GET `/api/products/search`：按名称模糊搜索，支持分页 | 关键词参数 | 输出：`app/api/products.py` | B3.4 | P0 |
| B3.7 | 购物车 Schema 与 API | 创建 `app/schemas/cart.py`，实现 `/api/cart`：GET（获取）、POST（添加）、PUT（更新数量）、DELETE（删除单项）、DELETE /clear（清空）| Token（USER） | 输出：`app/api/cart.py` | M1 | P0 |
| B3.8 | 创建订单 API | POST `/api/orders`：校验库存 → 计算总金额（含配送费）→ 创建 Order + OrderItem → 扣减 Product 库存 → 扣减钱包余额（预冻结） | `OrderCreateRequest` | 输出：`app/api/orders.py` | B3.7 | P0 |
| B3.9 | 模拟支付 API | POST `/api/orders/:id/pay`：校验订单状态 → 钱包余额确认 → 扣除钱包余额 → 状态流转至 PAID → 触发订单通知 | Token（USER） | 输出：`app/api/orders.py` | B3.8 | P0 |
| B3.10 | 订单查询 API | GET `/api/orders`：按 status 筛选、分页；GET `/api/orders/:id`：详情（含 OrderItem 列表） | Token | 输出：`app/api/orders.py` | B3.9 | P0 |
| B3.11 | 商家接单/拒单 API | PUT `/api/shops/orders/:id/accept`（ACCEPTED）/reject（CANCELLED，退款到钱包）| Token（SHOP_OWNER） | 输出：`app/api/shop_orders.py` | B3.8 | P0 |
| B3.12 | 商家备餐状态 API | PUT `/api/shops/orders/:id/prepare`（PREPARING）/ready（READY_FOR_PICKUP）| Token（SHOP_OWNER） | 输出：`app/api/shop_orders.py` | B3.11 | P0 |
| B3.13 | 轻量级状态轮询 API | GET `/api/orders/:id/status`：仅返回 order.id, order.status, order.updated_at 三个字段 | Token | 输出：`app/api/orders.py` | B3.10 | P1 |

#### 前端（9 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F3.1 | API 服务层扩展 | 创建 `src/services/order.ts`, `src/services/cart.ts`, `src/services/address.ts` | B3.1-B3.13 | 输出：`src/services/*.ts` | M1 | P0 |
| F3.2 | 消费者首页 | `/`：商家列表（卡片形式，含logo/名称/评分/距离/起送价），顶部搜索框 | UI 设计稿 | 输出：`src/pages/user/Home/` | F3.1 | P0 |
| F3.3 | 商家详情页 | `/shop/:id`：店铺头部信息（logo/公告/营业时间）+ 左侧分类 Tab + 右侧商品列表 + 底部购物栏 | UI 设计稿 | 输出：`src/pages/user/ShopDetail/` | F3.1 | P0 |
| F3.4 | 购物车页面 | `/cart`：购物车商品列表、数量步进器、删除、清空、金额明细（商品小计+配送费+总计）| UI 设计稿 | 输出：`src/pages/user/Cart/` | F3.1 | P0 |
| F3.5 | 收货地址管理页面 | `/addresses`：地址列表卡片（默认地址高亮）、新增/编辑弹窗表单、删除确认 | UI 设计稿 | 输出：`src/pages/user/Addresses/` | F3.1 | P0 |
| F3.6 | 确认订单页面 | `/order/confirm`：地址选择、商品明细、配送费展示、备注输入、提交订单按钮 | UI 设计稿 | 输出：`src/pages/user/OrderConfirm/` | F3.1 | P0 |
| F3.7 | 模拟支付页面 | `/order/pay/:id`：支付确认页，点击"立即支付" → 调用模拟支付 API → 成功跳转订单详情 | UI 设计稿 | 输出：`src/pages/user/OrderPay/` | F3.6 | P0 |
| F3.8 | 订单列表页面 | `/orders`：Tab 栏（全部/待支付/备餐中/配送中/已完成）、订单卡片列表 | UI 设计稿 | 输出：`src/pages/user/Orders/` | F3.1 | P0 |
| F3.9 | 订单详情页面 | `/order/:id`：订单状态时间线（垂直步骤条）、商品明细、配送信息、操作按钮（取消/确认收货）| UI 设计稿 | 输出：`src/pages/user/OrderDetail/` | F3.1 | P0 |
| F3.10 | 商家订单管理页面 | `/shop/orders`：Tab 栏（待接单/备餐中/已完成）、订单卡片、接单/拒单/备餐完成按钮 | UI 设计稿 | 输出：`src/pages/shop/Orders/` | F3.1 | P0 |

---

### M4 — 骑手配送

#### 后端（10 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B4.1 | 骑手待接单列表 API | GET `/api/rider/orders`：返回所有 READY_FOR_PICKUP 状态的订单，含商家地址/距离/配送费/用户地址 | Token（RIDER） | 输出：`app/api/rider.py` | M1 | P0 |
| B4.2 | 骑手接单 API | PUT `/api/rider/orders/:id/accept`：绑定 rider_id、状态→RIDER_PICKED_UP、记录接单时间 | Token（RIDER） | 输出：`app/api/rider.py` | B4.1 | P0 |
| B4.3 | 骑手取餐确认 API | PUT `/api/rider/orders/:id/pickup`：状态→DELIVERING、记录取餐时间 | Token（RIDER） | 输出：`app/api/rider.py` | B4.2 | P0 |
| B4.4 | 骑手送达确认 API | PUT `/api/rider/orders/:id/deliver`：状态→DELIVERED、记录送达时间、创建 RiderEarning 记录配送费收入 | Token（RIDER） | 输出：`app/api/rider.py` | B4.3 | P0 |
| B4.5 | 骑手进行中订单 API | GET `/api/rider/active`：返回当前骑手所有进行中订单（RIDER_PICKED_UP/DELIVERING）| Token（RIDER） | 输出：`app/api/rider.py` | B4.2 | P0 |
| B4.6 | 骑手收入明细 API | GET `/api/rider/earnings`：分页返回收入记录列表（order_no/amount/type/created_at）| Token（RIDER） | 输出：`app/api/rider.py` | B4.4 | P0 |
| B4.7 | 骑手累计收入 API | GET `/api/rider/earnings/summary`：返回累计收入总额 | Token（RIDER） | 输出：`app/api/rider.py` | B4.6 | P0 |
| B4.8 | 模拟提现 API | POST `/api/rider/withdraw`：校验余额 → 创建 WithdrawalRecord（直接 status=COMPLETED）→ 扣除钱包余额 | Token（RIDER） | 输出：`app/api/rider.py` | B4.7 | P0 |
| B4.9 | 消费者确认收货 API | PUT `/api/orders/:id/confirm`：状态→COMPLETED（仅 DELIVERED 状态可操作）| Token（USER） | 输出：`app/api/orders.py` | B4.4 | P0 |
| B4.10 | 提现记录查询 API | GET `/api/rider/withdraw/records`：骑手查看提现历史 | Token（RIDER） | 输出：`app/api/rider.py` | B4.8 | P0 |

#### 前端（6 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F4.1 | API 服务层扩展 | 创建 `src/services/rider.ts` | B4.1-B4.10 | 输出：`src/services/rider.ts` | M1 | P0 |
| F4.2 | 骑手待接单页面 | `/rider/orders`：订单卡片列表（距离/配送费/取货地址），接单按钮 | UI 设计稿 | 输出：`src/pages/rider/Orders/` | F4.1 | P0 |
| F4.3 | 骑手进行中页面 | `/rider/active`：进行中订单卡片、取餐确认按钮、送达确认按钮、商家/用户联系方式 | UI 设计稿 | 输出：`src/pages/rider/Active/` | F4.1 | P0 |
| F4.4 | 骑手收入页面 | `/rider/earnings`：累计收入展示卡片 + 收入明细列表（时间/订单号/金额）| UI 设计稿 | 输出：`src/pages/rider/Earnings/` | F4.1 | P0 |
| F4.5 | 骑手提现页面 | `/rider/withdraw`：可提现余额展示 + 提现表单（金额/方式/账号）+ 提现记录列表 | UI 设计稿 | 输出：`src/pages/rider/Withdraw/` | F4.1 | P0 |
| F4.6 | 订单状态轮询 | 在订单详情页面中实现 `setInterval` 每 5 秒调用 GET `/api/orders/:id/status`，自动更新状态时间线 | — | 输出：`src/pages/user/OrderDetail/` | F3.9 | P0 |

---

### M5 — 评价与管理

#### 后端（6 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B5.1 | 评价 Schema 与 API | 创建 `app/schemas/review.py`，POST `/api/reviews`：仅 DELIVERED/COMPLETED 订单可评价，创建 Review 记录，触发店铺评分更新（计算平均值写入 shops.rating）| Token（USER） | 输出：`app/api/reviews.py` | M3 | P0 |
| B5.2 | 评价列表 API | GET `/api/shops/:id/reviews`：分页返回店铺所有评价（含用户昵称）| — | 输出：`app/api/reviews.py` | B5.1 | P0 |
| B5.3 | 管理员用户列表 API | GET `/api/admin/users`：分页+手机号搜索，禁用/启用用户 PUT `/api/admin/users/:id/status` | Token（ADMIN） | 输出：`app/api/admin.py` | M1 | P0 |
| B5.4 | 管理员平台统计 API | GET `/api/admin/stats`：返回 total_orders, total_users, total_shops, today_orders 等统计数字 | Token（ADMIN） | 输出：`app/api/admin.py` | M3 | P0 |
| B5.5 | 管理员订单列表 API | GET `/api/admin/orders`：全平台订单列表，支持分页+状态筛选 | Token（ADMIN） | 输出：`app/api/admin.py` | M3 | P0 |
| B5.6 | 钱包余额查询 API | GET `/api/users/wallet`：返回钱包余额 | Token | 输出：`app/api/users.py` | M1 | P1 |

#### 前端（4 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F5.1 | API 服务层扩展 | 创建 `src/services/review.ts`, `src/services/admin.ts` | B5.1-B5.5 | 输出：`src/services/*.ts` | M1 | P0 |
| F5.2 | 评价页面 | `/order/:id/review`：星级评分组件（双栏：商家+骑手）、文字评价输入、图片上传按钮 | UI 设计稿 | 输出：`src/pages/user/Review/` | F5.1 | P0 |
| F5.3 | 商家详情页评价展示 | 在商家详情页 `/shop/:id` 底部追加评价列表 Tab，展示评分和评价内容 | UI 设计稿 | 输出：`src/pages/user/ShopDetail/` | F5.1 | P0 |
| F5.4 | 管理员仪表盘 | `/admin/dashboard`：统计卡片（订单量/用户数/商家数/今日订单）+ 近7日趋势图（Ant Design Charts）| UI 设计稿 | 输出：`src/pages/admin/Dashboard/` | F5.1 | P0 |
| F5.5 | 管理员用户管理页面 | `/admin/users`：用户列表表格（分页+搜索）、状态标签、禁用/启用按钮 | UI 设计稿 | 输出：`src/pages/admin/Users/` | F5.1 | P0 |

---

### M6 — 打磨优化

#### 后端（6 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| B6.1 | 全局异常处理 | 在 `app/main.py` 中注册 `exception_handlers`，统一捕获 HTTPException, RequestValidationError, 未知异常，返回格式化错误响应 | — | 输出：`app/main.py` | M1 | P0 |
| B6.2 | 请求参数校验增强 | 使用 Pydantic Field 添加详细校验消息（如 @field_validator 校验手机号格式、金额非负等）| — | 输出：`app/schemas/*.py` | M1 | P1 |
| B6.3 | 后端单元测试 | 使用 pytest + pytest-asyncio 编写核心业务测试：认证流程、订单创建、支付、状态流转、骑手收入计算，覆盖率≥60% | 核心业务代码 | 输出：`tests/` | M1-M5 | P1 |
| B6.4 | Alembic 迁移脚本规范化 | 为每个里程碑编写迁移脚本，添加正向迁移和回滚脚本（down_revision）| 各里程碑数据模型变更 | 输出：`alembic/versions/` | M2-M5 | P2 |
| B6.5 | 种子数据脚本 | 创建 `scripts/seed_data.py`：生成示例商家（5个）、商品（各10个）、测试用户（各类角色各1个）、示例订单 | — | 输出：`scripts/seed_data.py` | M3 | P2 |
| B6.6 | OpenAPI 文档补充 | 为所有 API 路由添加 docstring（摘要、参数说明、响应示例）| — | 输出：`app/api/*.py` | M5 | P2 |

#### 前端（7 项）

| # | 任务标题 | 执行内容 | 输入/输出 | 依赖 | 优先级 |
|---|----------|----------|-----------|------|--------|
| F6.1 | 全局错误提示 | 创建 `src/components/ErrorBoundary.tsx` + `src/hooks/useNotification.ts`，全局捕获 React Error Boundary 和 Axios 错误，统一显示 AntD message/notification | — | 输出：`src/components/`, `src/hooks/` | M1 | P0 |
| F6.2 | 表单校验完善 | 在所有表单页面（登录/注册/开店/商品等）添加 AntD Form 校验规则，与后端 Pydantic 校验对齐 | — | 输出：各表单页面 | M1 | P1 |
| F6.3 | 加载态与空状态 | 为所有列表页面添加 `Loading` 骨架屏（AntD Skeleton）和 `Empty` 空状态组件 | — | 输出：各列表页面 | M2 | P1 |
| F6.4 | 响应式布局 | 使用 AntD `Grid` (Row/Col) + `Responsive` 调整消费者端和骑手端移动端适配，设置断点 576px/768px/992px | — | 输出：主要页面组件 | M3 | P1 |
| F6.5 | 个人中心页面 | `/profile`：头像上传、昵称修改、钱包余额展示、退出登录 | UI 设计稿 | 输出：`src/pages/user/Profile/` | M1 | P2 |
| F6.6 | 前端单元测试 | 使用 Vitest + React Testing Library 编写组件测试：登录流程、表单校验、订单列表渲染 | 核心组件 | 输出：`frontend/tests/` | M1-M5 | P1 |
| F6.7 | README 开发文档完善 | 补充本地开发详细步骤、数据库迁移命令、环境变量说明、常见问题 FAQ | — | 输出：`README.md` | M1 | P1 |

---

## 技术方案补充

### 1. 数据库连接配置

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,  # sqlite+aiosqlite:///./data.db 或 mysql+aiomysql://...
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### 2. JWT Token 结构

```python
# Token Payload
{
    "sub": str(user_id),
    "role": "USER" | "SHOP_OWNER" | "RIDER" | "ADMIN",
    "exp": datetime.timestamp() + 86400
}
```

### 3. 统一响应格式

```python
# 成功
{"code": 0, "message": "success", "data": {...}}
{"code": 0, "message": "success", "data": {"items": [], "total": 100, "page": 1, "page_size": 20}}
# 失败
{"code": 40001, "message": "手机号已注册", "data": null}
```

### 4. 订单号生成规则

```
时间戳(13位) + 随机数(6位)  →  示例：20260301123456789ABCDEF
```

### 5. 配送费计算公式

```
if distance <= 3:
    fee = 3.0
else:
    fee = 3.0 + (distance - 3) * 1.0

# 封顶
fee = min(fee, 3.0 + 7 * 1.0) = 10.0  # 最大配送费 10 元
```

### 6. 前端目录结构建议

```
frontend/src/
├── api/           # 按模块拆分 API
├── assets/        # 静态资源
├── components/    # 通用组件
├── hooks/         # 自定义 Hooks
├── layouts/       # 布局组件
├── pages/         # 页面组件
│   ├── user/      # 消费者
│   ├── shop/      # 商家
│   ├── rider/     # 骑手
│   └── admin/     # 管理员
├── services/      # API 服务封装
├── stores/        # Zustand 状态
├── styles/        # 全局样式
├── types/         # TypeScript 类型定义
└── utils/         # 工具函数
```

### 7. Git 分支策略

```
main              # 主分支，保护分支
├── develop       # 开发主分支
│   ├── feature/m1-backend-auth
│   ├── feature/m1-frontend-scaffold
│   ├── feature/m2-shop-management
│   └── ...
└── release/       # 发布分支
```

---

## 任务统计汇总

| 里程碑 | 后端任务 | 前端任务 | DevOps | 合计 |
|--------|----------|----------|--------|------|
| M1 | 15 | 10 | 2 | 27 |
| M2 | 7 | 6 | 0 | 13 |
| M3 | 13 | 10 | 0 | 23 |
| M4 | 10 | 6 | 0 | 16 |
| M5 | 6 | 5 | 0 | 11 |
| M6 | 6 | 7 | 0 | 13 |
| **总计** | **57** | **44** | **2** | **103** |

---

## 开发优先级说明

- **P0**：MVP 必须完成，否则核心流程无法跑通
- **P1**：重要功能，影响用户体验，但不阻塞核心闭环
- **P2**：优化项，可在上线后持续迭代

---

## 已实现 API 清单

### 认证模块（auth.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/logout` | 用户登出 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |

### 用户模块（users.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户信息 |
| PUT | `/api/v1/users/me` | 更新用户信息 |
| POST | `/api/v1/users/addresses` | 添加收货地址 |
| GET | `/api/v1/users/addresses` | 获取地址列表 |
| PUT | `/api/v1/users/addresses/{id}` | 更新地址 |
| DELETE | `/api/v1/users/addresses/{id}` | 删除地址 |

### 商家模块（shop.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/shop/apply` | 申请开店 |
| GET | `/api/v1/shop/my` | 获取我的店铺 |
| PUT | `/api/v1/shop/my` | 更新店铺信息 |
| GET | `/api/v1/shop/list` | 商家列表 |
| GET | `/api/v1/shop/{shop_id}` | 商家详情 |
| POST | `/api/v1/shop/category` | 创建分类 |
| GET | `/api/v1/shop/category/{shop_id}` | 分类列表 |
| PUT | `/api/v1/shop/category/{category_id}` | 更新分类 |
| DELETE | `/api/v1/shop/category/{category_id}` | 删除分类 |
| POST | `/api/v1/shop/product` | 创建商品 |
| GET | `/api/v1/shop/product/{shop_id}` | 商品列表 |
| GET | `/api/v1/shop/product/detail/{product_id}` | 商品详情 |
| PUT | `/api/v1/shop/product/{product_id}` | 更新商品 |
| DELETE | `/api/v1/shop/product/{product_id}` | 删除商品 |
| GET | `/api/v1/shop/search` | 商品搜索 |
| GET | `/api/v1/shop/my/orders` | 商家订单列表 |
| GET | `/api/v1/shop/my/orders/{order_id}` | 商家订单详情 |
| PUT | `/api/v1/shop/my/orders/{order_id}/accept` | 接单 |
| PUT | `/api/v1/shop/my/orders/{order_id}/reject` | 拒单 |
| PUT | `/api/v1/shop/my/orders/{order_id}/ready` | 备餐完成 |
| GET | `/api/v1/shop/my/stats` | 商家统计 |
| GET | `/api/v1/shop/my/stats/trend` | 商家趋势 |

### 订单模块（orders.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/orders` | 创建订单 |
| GET | `/api/v1/orders` | 订单列表 |
| GET | `/api/v1/orders/{order_id}` | 订单详情 |
| POST | `/api/v1/orders/{order_id}/pay` | 支付订单 |
| PUT | `/api/v1/orders/{order_id}/cancel` | 取消订单 |
| PUT | `/api/v1/orders/{order_id}/confirm` | 确认收货 |

### 骑手模块（rider.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/rider/orders` | 待接单列表 |
| PUT | `/api/v1/rider/orders/{order_id}/accept` | 骑手接单 |
| PUT | `/api/v1/rider/orders/{order_id}/pickup` | 取餐确认 |
| PUT | `/api/v1/rider/orders/{order_id}/deliver` | 送达确认 |
| GET | `/api/v1/rider/active` | 进行中订单 |
| GET | `/api/v1/rider/earnings` | 收入明细 |
| GET | `/api/v1/rider/earnings/summary` | 累计收入 |
| POST | `/api/v1/rider/withdraw` | 提现申请 |
| GET | `/api/v1/rider/withdraw/records` | 提现记录 |

### 钱包模块（wallet.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/wallet/balance` | 查询余额 |
| POST | `/api/v1/wallet/recharge` | 充值 |
| GET | `/api/v1/wallet/transactions` | 交易记录 |

### 管理员模块（admin.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/users` | 用户列表 |
| PUT | `/api/v1/admin/users/{user_id}/status` | 用户状态 |
| GET | `/api/v1/admin/shop/pending` | 待审核商家 |
| PUT | `/api/v1/admin/shop/{shop_id}/approve` | 审核通过 |
| PUT | `/api/v1/admin/shop/{shop_id}/reject` | 审核拒绝 |
| GET | `/api/v1/admin/orders` | 订单列表 |
| GET | `/api/v1/admin/stats` | 平台统计 |

### 评价模块（review.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/review` | 创建评价 |
| GET | `/api/v1/review/shop/{shop_id}` | 店铺评价 |

### 优惠券模块（coupons.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/coupons` | 创建优惠券 |
| GET | `/api/v1/coupons` | 优惠券列表 |
| POST | `/api/v1/coupons/{coupon_id}/claim` | 领取优惠券 |
| GET | `/api/v1/coupons/my` | 我的优惠券 |

### 收藏模块（favorites.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/favorites` | 添加收藏 |
| DELETE | `/api/v1/favorites/{shop_id}` | 取消收藏 |
| GET | `/api/v1/favorites` | 我的收藏 |

### 审核日志模块（audit.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/audit/logs` | 操作日志 |
| GET | `/api/v1/audit/finance` | 财务日志 |

### 配置模块（config.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/config` | 获取配置 |
| PUT | `/api/v1/config` | 更新配置 |

### 上传模块（upload.py）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/upload` | 文件上传 |

---

## 数据模型清单

### 用户相关
| 模型 | 表名 | 说明 |
|------|------|------|
| User | users | 用户表 |
| UserAddress | user_addresses | 收货地址 |
| Wallet | wallets | 钱包 |
| Favorite | favorites | 收藏 |

### 商家相关
| 模型 | 表名 | 说明 |
|------|------|------|
| Shop | shops | 店铺 |
| Category | categories | 分类 |
| Product | products | 商品 |

### 订单相关
| 模型 | 表名 | 说明 |
|------|------|------|
| Order | orders | 订单 |
| OrderItem | order_items | 订单项 |
| CartItem | cart_items | 购物车项 |

### 评价相关
| 模型 | 表名 | 说明 |
|------|------|------|
| Review | reviews | 评价 |

### 骑手相关
| 模型 | 表名 | 说明 |
|------|------|------|
| RiderEarning | rider_earnings | 骑手收入 |
| WithdrawalRecord | withdrawal_records | 提现记录 |

### 支付财务相关
| 模型 | 表名 | 说明 |
|------|------|------|
| PaymentTransaction | payment_transactions | 支付交易 |
| ShopEarning | shop_earnings | 商家收益 |
| PlatformCommission | platform_commissions | 平台佣金 |
| FundFlow | fund_flows | 资金流水 |
| RefundRecord | refund_records | 退款记录 |

### 优惠券相关
| 模型 | 表名 | 说明 |
|------|------|------|
| Coupon | coupons | 优惠券 |
| UserCoupon | user_coupons | 用户优惠券 |

### 系统相关
| 模型 | 表名 | 说明 |
|------|------|------|
| PlatformConfig | platform_configs | 平台配置 |
| AuditLog | audit_logs | 操作日志 |
| FinanceAuditLog | finance_audit_logs | 财务日志 |

---

*文档版本：V2.0（2026-05-20）*
*更新说明：新增实现状态概览、完整API清单、数据模型清单*

---
