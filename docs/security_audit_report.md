# FuYellowBlueRed 安全审计报告

> 版本: v1.0 | 日期: 2026-05-16 | 审计人: 安全专家 | 状态: 初稿

---

## 一、执行摘要

本报告对 FuYellowBlueRed 外卖配送平台进行了全面的代码安全审计，涵盖后端 Python/FastAPI 和前端 React/TypeScript 代码。审计发现了 **5 个严重安全问题**、**8 个高危问题**、**12 个中危问题** 和 **6 个低危问题**。

**关键风险**：
1. 支付接口缺乏幂等性保护和金额上限，存在资金损失风险
2. 文件上传未验证类型，可导致恶意文件上传
3. 钱包充值接口权限控制不当，任意用户可给自己充值

---

## 二、严重问题（Critical）

### SEC-001: 支付/充值无限额

**严重程度**: 🔴 Critical  
**影响**: 可导致平台资金损失

**问题位置**: 
- [wallet.py:48-78](file:///workspace/backend/app/api/v1/wallet.py#L48-L78) - 充值接口无上限
- [finance.py:62-104](file:///workspace/backend/app/services/finance.py#L62-L104) - 支付无幂等性保护

**问题描述**:
```python
# wallet.py - 充值金额无上限
@router.post("/recharge", response_model=ResponseSchema[dict])
async def recharge_wallet(amount: float, ...):
    if amount <= 0:
        raise BadRequestException("充值金额必须大于0")
    # ❌ 无限额！攻击者可充值任意金额
```

```python
# finance.py - 支付无幂等性
async def process_payment(db, order, user, channel):
    # ❌ 未检查订单是否已支付，可重复扣款
    wallet.balance -= order.total_amount
```

**修复建议**:
1. 充值设置每日/单笔上限：`if amount > MAX_RECHARGE: raise BadRequestException`
2. 支付前检查订单状态：`if payment_exists(order_id): raise BadRequestException("已支付")`
3. 使用数据库唯一约束防止重复支付

**业务影响**: 高 - 必须立即修复

---

### SEC-002: 文件上传无类型验证

**严重程度**: 🔴 Critical  
**影响**: 可上传恶意文件，导致服务器被入侵

**问题位置**: [upload.py:14-37](file:///workspace/backend/app/api/v1/upload.py#L14-L37)

**问题描述**:
```python
@router.post("", response_model=ResponseSchema[str])
async def upload_file(file: UploadFile = File(...), ...):
    # ❌ 未验证文件类型
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    # ❌ 可上传 .php, .exe, .py 等恶意文件
```

**修复建议**:
```python
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

ext = os.path.splitext(file.filename)[1].lower()
if ext not in ALLOWED_EXTENSIONS:
    raise BadRequestException("不支持的文件类型")
if file.content_type not in ALLOWED_CONTENT_TYPES:
    raise BadRequestException("文件类型不匹配")
```

**业务影响**: 高 - 必须立即修复

---

### SEC-003: JWT Secret Key 硬编码默认值

**严重程度**: 🔴 Critical  
**影响**: 攻击者可伪造任意用户身份

**问题位置**: [config.py:9](file:///workspace/backend/app/config.py#L9)

**问题描述**:
```python
SECRET_KEY: str = "your-super-secret-key-change-in-production"
```

**修复建议**:
1. 强制要求环境变量设置密钥
2. 启动时检查是否为默认值并拒绝启动
3. 生产环境使用 256 位随机密钥

```python
import secrets
if settings.SECRET_KEY == "your-super-secret-key-change-in-production":
    if not settings.DEBUG:
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
```

**业务影响**: 高 - 必须立即修复

---

### SEC-004: 钱包充值权限控制缺陷

**严重程度**: 🔴 Critical  
**影响**: 普通用户可给自己无限充值，伪造资金

**问题位置**: [wallet.py:48-78](file:///workspace/backend/app/api/v1/wallet.py#L48-L78)

**问题描述**:
```python
# 模拟充值接口被普通用户调用
@router.post("/recharge", response_model=ResponseSchema[dict])
async def recharge_wallet(amount: float, current_user: User = Depends(get_current_user), ...):
    # ❌ 任何登录用户都可以给自己充值任意金额！
    wallet.balance += amount
```

**修复建议**:
1. 移除用户自主充值接口（仅管理员可操作）
2. 或接入真实支付网关（支付宝/微信）
3. 添加充值记录和审核机制

**业务影响**: 高 - 必须立即修复

---

### SEC-005: 账务操作事务不完整

**严重程度**: 🔴 Critical  
**影响**: 数据库操作可能部分成功，导致数据不一致

**问题位置**: [finance.py:62-104](file:///workspace/backend/app/services/finance.py#L62-L104), [wallet.py:48-78](file:///workspace/backend/app/api/v1/wallet.py#L48-L78)

**问题描述**:
```python
# finance.py - 多处单独 commit
wallet.balance -= order.total_amount  # 修改1
await FinanceService.create_fund_flow(...)  # 新增记录
db.add(payment)  # 新增支付记录
# ❌ 如果 create_fund_flow 失败，余额已扣但无记录

# wallet.py - 多次 commit
wallet.balance += amount
await FinanceService.create_fund_flow(...)  # 内部 commit
await db.commit()  # 再次 commit
await db.refresh(wallet)  # 可能刷新失败
```

**修复建议**:
1. 所有相关操作在同一事务中
2. 使用 savepoint 控制嵌套事务
3. 统一事务边界

```python
async def process_payment(db, order, user, channel):
    try:
        wallet.balance -= order.total_amount
        await FinanceService.create_fund_flow(...)
        db.add(payment)
        await db.commit()  # 统一提交
    except Exception:
        await db.rollback()  # 统一回滚
        raise
```

**业务影响**: 高 - 必须立即修复

---

## 三、高危问题（High）

### SEC-006: 密码强度无验证

**严重程度**: 🟠 High  
**位置**: [auth.py:26-32](file:///workspace/backend/app/api/v1/auth.py#L26-L32)

**问题**: 用户可注册极弱密码如 "123"

**建议**: 添加密码强度校验
```python
import re
def validate_password(password: str):
    if len(password) < 8:
        raise BadRequestException("密码至少8位")
    if not re.search(r'[A-Za-z]', password):
        raise BadRequestException("密码需包含字母")
    if not re.search(r'\d', password):
        raise BadRequestException("密码需包含数字")
```

---

### SEC-007: 登录无限制（暴力破解风险）

**严重程度**: 🟠 High  
**位置**: [auth.py:49-62](file:///workspace/backend/app/api/v1/auth.py#L49-L62)

**问题**: 无登录尝试次数限制、无验证码

**建议**: 
1. 添加登录失败次数限制（5次后锁定15分钟）
2. 添加图形验证码或短信验证码
3. 记录登录失败日志用于监控

---

### SEC-008: 管理员可修改任意用户状态

**严重程度**: 🟠 High  
**位置**: [admin.py:154-176](file:///workspace/backend/app/api/v1/admin.py#L154-L176)

**问题**: admin可禁用任意用户，包括其他管理员

**建议**: 添加权限层级，防止管理员互删

---

### SEC-009: SQL注入风险（潜在）

**严重程度**: 🟠 High  
**位置**: [shop.py:124-126](file:///workspace/backend/app/api/v1/shop.py#L124-L126)

**问题**: 使用 `.contains()` 进行模糊搜索
```python
stmt = stmt.where(Shop.name.contains(query.keyword))
```

**说明**: SQLAlchemy 会自动转义，但建议统一使用参数化查询模式

---

### SEC-010: 敏感信息日志记录

**严重程度**: 🟠 High  
**位置**: 多处 logger.info()

**问题**:
```python
logger.info(f"User logged in successfully: {user.id}")
logger.info(f"Wallet recharged: user={current_user.id}, amount={amount}")
```

**建议**: 
1. 脱敏处理：只记录 user.id，不记录金额详情
2. 禁止记录密码、token、银行卡号等

---

### SEC-011: CORS配置过于宽松

**严重程度**: 🟠 High  
**位置**: [config.py:12](file:///workspace/backend/app/config.py#L12), [main.py:49-55](file:///workspace/backend/app/main.py#L49-L55)

**问题**: 
```python
CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
# 生产环境可能未修改
```

**建议**: 
1. 生产环境严格限制来源
2. 使用环境变量区分开发/生产配置

---

### SEC-012: 错误信息泄露

**严重程度**: 🟠 High  
**位置**: 全局异常处理

**问题**: 
```python
return JSONResponse(content={"message": str(exc), "trace": traceback})
```

**建议**: 生产环境隐藏详细错误，仅记录日志

---

### SEC-013: 缺少账户锁定机制

**严重程度**: 🟠 High  
**位置**: [auth.py](file:///workspace/backend/app/api/v1/auth.py)

**问题**: 密码连续错误不锁定账户

**建议**: 添加连续失败锁定逻辑

---

## 四、中危问题（Medium）

### SEC-014: 前端 Token 存储风险

**严重程度**: 🟡 Medium  
**位置**: [api.ts:14-16](file:///workspace/frontend/src/services/api.ts#L14-L16)

**问题**: Token 存储在 localStorage，易受 XSS 攻击

**建议**: 使用 httpOnly Cookie 存储，或加密后存储

---

### SEC-015: 缺少 HTTPS 强制

**严重程度**: 🟡 Medium  
**位置**: [config.py](file:///workspace/backend/app/config.py)

**问题**: 未强制 HTTPS

**建议**: 生产环境添加 HTTPS 重定向

---

### SEC-016: 缺少安全响应头

**严重程度**: 🟡 Medium  
**位置**: [main.py](file:///workspace/backend/app/main.py)

**建议**: 添加以下响应头：
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000

---

### SEC-017: 文件上传大小限制可绕过

**严重程度**: 🟡 Medium  
**位置**: [upload.py:19](file:///workspace/backend/app/api/v1/upload.py#L19)

**问题**: 仅检查 file.size，未限制实际读取大小

---

### SEC-018: 订单号可枚举

**严重程度**: 🟡 Medium  
**位置**: [orders.py](file:///workspace/backend/app/api/v1/orders.py)

**问题**: 订单 ID 使用自增整数

**建议**: 使用 UUID 或随机字符串

---

### SEC-019: 缺少操作审计日志

**严重程度**: 🟡 Medium  
**位置**: 全局

**建议**: 关键操作（充值、提现、管理）需完整审计

---

### SEC-020: 会话管理不完善

**严重程度**: 🟡 Medium  
**位置**: [auth.py](file:///workspace/backend/app/api/v1/auth.py)

**问题**: 无登录设备管理、无主动下线功能

---

### SEC-021: 商家可操作任意订单

**严重程度**: 🟡 Medium  
**位置**: [shop.py:441-469](file:///workspace/backend/app/api/v1/shop.py#L441-L469)

**问题**: 订单关联检查可能存在绕过

---

### SEC-022: 缺少速率限制中间件

**严重程度**: 🟡 Medium  
**位置**: [main.py](file:///workspace/backend/app/main.py)

**问题**: 虽然引入了 slowapi，但未对所有接口应用限制

---

### SEC-023: 密码重置无验证

**严重程度**: 🟡 Medium  
**位置**: 缺少密码重置功能

**建议**: 实现邮箱/短信验证码重置

---

### SEC-024: 第三方依赖安全

**严重程度**: 🟡 Medium  
**位置**: requirements.txt

**建议**: 定期更新依赖，扫描漏洞

---

## 五、低危问题（Low）

### SEC-025: 前端敏感数据暴露

**严重程度**: ⚪ Low  
**位置**: [Profile.tsx](file:///workspace/frontend/src/pages/user/Profile.tsx#L48-L52)

**问题**: 页面直接显示手机号

---

### SEC-026: 缺少安全开发文档

**严重程度**: ⚪ Low

**建议**: 添加安全开发规范文档

---

### SEC-027: 缺少渗透测试

**严重程度**: ⚪ Low

**建议**: 定期进行专业渗透测试

---

### SEC-028: 日志保留策略不明确

**严重程度**: ⚪ Low

**建议**: 明确日志保留期限

---

### SEC-029: 备份策略不明确

**严重程度**: ⚪ Low

**建议**: 制定数据库备份策略

---

### SEC-030: 容器/部署安全配置

**严重程度**: ⚪ Low

**建议**: 容器运行时使用非 root 用户

---

## 六、安全需求清单（安全专家视角）

### 必须修复（P0）

| 需求ID | 需求描述 | 优先级 | 影响文件 |
|--------|---------|--------|---------|
| SEC-P0-01 | 支付接口添加幂等性保护 | Critical | finance.py, orders.py |
| SEC-P0-02 | 充值/支付添加金额上限 | Critical | wallet.py, finance.py |
| SEC-P0-03 | 文件上传类型白名单验证 | Critical | upload.py |
| SEC-P0-04 | JWT密钥环境变量强制检查 | Critical | config.py |
| SEC-P0-05 | 移除或限制用户自主充值 | Critical | wallet.py |
| SEC-P0-06 | 账务操作事务一致性改造 | Critical | finance.py, wallet.py |

### 高优先级（P1）

| 需求ID | 需求描述 | 优先级 | 影响文件 |
|--------|---------|--------|---------|
| SEC-P1-01 | 密码强度校验 | High | auth.py |
| SEC-P1-02 | 登录失败次数限制 | High | auth.py |
| SEC-P1-03 | 敏感日志脱敏 | High | 全局 |
| SEC-P1-04 | 生产环境CORS严格配置 | High | config.py, main.py |
| SEC-P1-05 | 错误信息不暴露详情 | High | main.py |
| SEC-P1-06 | 账户连续失败锁定 | High | auth.py |

### 中优先级（P2）

| 需求ID | 需求描述 | 优先级 | 影响文件 |
|--------|---------|--------|---------|
| SEC-P2-01 | Token存储安全改造 | Medium | api.ts |
| SEC-P2-02 | 安全响应头添加 | Medium | main.py |
| SEC-P2-03 | 审计日志系统 | Medium | 全局 |
| SEC-P2-04 | 操作审计表 | Medium | models.py |
| SEC-P2-05 | 速率限制全面应用 | Medium | main.py |
| SEC-P2-06 | 依赖安全扫描 | Medium | requirements.txt |

### 低优先级（P3）

| 需求ID | 需求描述 | 优先级 | 影响文件 |
|--------|---------|--------|---------|
| SEC-P3-01 | 前端敏感数据脱敏 | Low | Profile.tsx |
| SEC-P3-02 | 安全开发文档 | Low | docs/ |
| SEC-P3-03 | 定期渗透测试 | Low | - |
| SEC-P3-04 | 容器安全配置 | Low | Dockerfile |

---

## 七、安全修复计划

### Phase 1: 紧急修复（1-2天）

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| 支付幂等性保护 | finance.py, orders.py | 2h |
| 充值金额上限 | wallet.py | 1h |
| 文件类型白名单 | upload.py | 1h |
| JWT密钥强制检查 | config.py | 1h |
| 账务事务一致性 | finance.py | 3h |

### Phase 2: 高优先级修复（3-5天）

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| 密码强度校验 | auth.py | 2h |
| 登录限流 | auth.py | 2h |
| 日志脱敏 | 全局 | 2h |
| CORS/错误处理 | config.py, main.py | 2h |
| 账户锁定 | auth.py | 2h |

### Phase 3: 中优先级修复（1周）

| 任务 | 涉及文件 | 预计工时 |
|------|---------|---------|
| Token安全存储 | api.ts | 3h |
| 安全响应头 | main.py | 1h |
| 审计日志 | models.py, 全局 | 5h |
| 速率限制完善 | main.py | 2h |

---

## 八、安全验收标准

### 功能验收
- [ ] 支付接口支持幂等（重复调用返回相同结果）
- [ ] 单笔充值上限 10,000 元
- [ ] 每日充值上限 50,000 元
- [ ] 仅支持图片文件上传（jpg/png/gif/webp）
- [ ] 生产环境 JWT 密钥必须通过环境变量配置
- [ ] 用户自主充值功能移除或管理员审批

### 安全验收
- [ ] 密码强度校验生效（8位以上，含字母数字）
- [ ] 连续5次登录失败锁定15分钟
- [ ] 日志中不包含敏感信息（金额完整数据）
- [ ] CORS 仅允许指定域名
- [ ] 错误响应不包含堆栈信息

### 安全测试
- [ ] SQL注入测试通过
- [ ] XSS攻击测试通过
- [ ] CSRF防护测试通过
- [ ] 暴力破解防护测试通过
- [ ] 文件上传绕过测试通过

---

## 九、风险评估矩阵

| 风险项 | 可能性 | 影响 | 风险值 | 缓解措施 |
|--------|--------|------|--------|---------|
| 恶意充值 | 高 | 严重 | 🔴 极高 | 移除用户充值，接入真实支付 |
| 重复扣款 | 高 | 严重 | 🔴 极高 | 幂等性保护 |
| 恶意文件上传 | 中 | 严重 | 🔴 高 | 类型白名单 |
| Token伪造 | 低 | 严重 | 🟠 高 | 密钥强制配置 |
| 暴力破解 | 高 | 中 | 🟠 高 | 登录限流 |
| 数据泄露 | 中 | 中 | 🟡 中 | 脱敏+审计 |
