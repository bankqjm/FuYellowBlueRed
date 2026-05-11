# FuYellowBlueRed 🍜

开源外卖配送平台 — 低佣金、透明结算、社区驱动

## 项目简介

FuYellowBlueRed 是一个开源的外卖配送平台，覆盖从用户下单到骑手配送的完整订单闭环。项目面向小型外卖团队、校园配送、社区团购等场景，提供可落地、可二次开发的技术方案。

### 核心特点

- **完整订单闭环**：消费者下单 → 商家接单备餐 → 骑手取餐配送 → 用户收货评价
- **多角色支持**：消费者、商家、骑手、管理员四端一体化
- **开源免费**：MIT 协议，核心功能永久免费
- **易于部署**：Docker Compose 一键启动

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React + Ant Design | 基于 AntD Pro，多角色统一入口 |
| 后端 | Python + FastAPI | 异步高性能，自动生成 API 文档 |
| 数据库 | MySQL / SQLite | 开发用 SQLite，生产推荐 MySQL |
| ORM | SQLAlchemy | Python 主流 ORM |
| 认证 | JWT (PyJWT) | 无状态 Token 鉴权 |
| 部署 | Docker + Docker Compose | 一键启动所有服务 |

## 项目结构

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
│   │   ├── services/        # API 调用
│   │   ├── stores/          # 状态管理
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── Dockerfile
├── docs/                     # 项目文档
│   └── requirements.md      # 需求规格说明书
├── docker-compose.yml
├── LICENSE
└── README.md
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+（或使用 SQLite）
- Docker & Docker Compose（可选）

### Docker 部署（推荐）

```bash
git clone https://github.com/bankqjm/FuYellowBlueRed.git
cd FuYellowBlueRed
docker-compose up -d
```

- 前端访问：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 本地开发

**后端**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

## 功能概览

### 消费者端

浏览商家、搜索商品、购物车、下单支付、订单跟踪、评价

### 商家端

店铺管理、商品分类管理、商品上下架、接单/拒单、备餐状态

### 骑手端

待接单列表、取餐确认、送达确认、收入明细、模拟提现

### 管理端

商家审核、用户管理、平台数据概览

## MVP 简化策略

| 模块 | 完整方案 | MVP 方案 |
|------|----------|----------|
| 支付 | 微信/支付宝 | 模拟支付 |
| 地图导航 | 地图 SDK | Haversine 距离计算 |
| 实时通信 | WebSocket | 前端轮询 |
| 部署 | 微服务 + K8s | 单机 Docker |
| 通知 | 短信/推送 | 站内消息 |
| 图片存储 | OSS/S3 | 本地文件 |

## 文档

- [MVP 需求规格说明书](docs/requirements.md)

## 开源协议

[MIT License](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request 参与项目贡献。
