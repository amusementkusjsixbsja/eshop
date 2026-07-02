# 电商平台 (E-Shop)

基于 Python FastAPI + React 的轻量级电商平台 Demo。
支持用户注册登录、商品浏览、购物车、下单支付、**5 分钟极速物流**、售后管理、**AI 智能客服**（Function Calling + 实时数据）和管理后台。

---

## 项目结构

| 模块 | 目录 | 技术栈 | 端口 | 负责人 |
|------|------|--------|------|--------|
| 用户与商品 | `service-user-product/` | Python FastAPI + PostgreSQL | 8001 | 小B |
| 购物车与交易 | `service-order-trade/` | FastAPI + PostgreSQL + APScheduler | 8002 | 小C |
| 管理后台 | `service-admin/` | Python FastAPI + PostgreSQL | 8003 | 小D |
| AI 客服 | `ai-service/` | FastAPI + LangChain + DeepSeek | 8004 | 小A |
| 前端 | `frontend/` | React 19 + Vite + TypeScript | 5173 | 小A |
| 共享库 | `shared/` | Python 基础库（DB/Redis/JWT） | — | 框架 |
| 基础设施 | `docker/` | Docker Compose + Nginx + init.sql | 80 | 小A |

## 快速启动

```bash
# 启动全部服务
docker compose -f docker/docker-compose.yml up -d

# 查看状态
docker compose -f docker/docker-compose.yml ps
```

访问 **http://localhost:80**（Nginx 统一入口）

前端独立开发：
```bash
cd frontend && npm install && npm run dev    # 端口 5173，热重载
```

---

## 预置账号

| 角色 | 邮箱 | 密码 | 说明 |
|------|------|------|------|
| 🛡️ 管理员 | admin@shop.local | admin123 | 可访问管理后台 |
| 👤 普通用户 | user@test.com | 123456 | 有预置地址和测试数据 |

> 测试时也可注册新用户：`curl -s http://localhost/api/shop/c-endpoint/auth/register -X POST -H "Content-Type: application/json" -d '{"email":"test@demo.com","password":"123456","nickname":"Demo"}'`

---

## 功能清单

### 🛍️ 用户端（C 端）

| 功能 | 说明 |
|------|------|
| 注册/登录 | bcrypt 加密 + JWT 无状态认证 |
| 商品浏览 | 分类筛选 / 关键词搜索 / 热门推荐（Redis 缓存） |
| 购物车 | 添加/修改/删除/叠加数量，下单自动清空 |
| 下单支付 | 事务锁库存 → 扣减 → 创建订单 → 清购物车 → 支付记录 |
| **5 分钟极速物流** | 支付后每 1 分钟推进一个节点，前端 15s 轮询实时更新 |
| 售后中心 | 退款/退货/换货申请与状态跟踪 |
| 地址管理 | 多地址 CRUD、默认地址切换、购物车地址选择器 |
| AI 智能客服 🤖 | Function Calling + 实时业务数据查询（见下方） |

### 🔧 管理后台（B 端 — 需 admin 角色）

| 功能 | 说明 |
|------|------|
| 分类管理 | 增删改（带子分类/商品引用保护）+ Redis 缓存清除 |
| 商品管理 | 增删改、上下架、按分类筛癣缓存清除 |
| 订单管理 | 所有用户订单查看、按状态筛癣用户昵称显示 |

### 🤖 AI 客服系统

| 能力 | 详情 |
|------|------|
| 身份识别 | 解析 JWT 自动获取当前用户信息 |
| 工具调用 | 查订单、查物流、查售后、搜商品、查用户信息 |
| 数据源 | 通过内部接口调用 user-product 和 order-trade 获取**真实数据** |
| 流式输出 | SSE 逐 token 输出，实时打字效果 |
| 对话记忆 | 多轮上下文，支持追问 |

---

## 架构图

```
用户 → Nginx (:80)
  ├── /api/shop/c-endpoint/auth/*     → user-product:8001   # 认证
  ├── /api/shop/c-endpoint/products/* → user-product:8001   # 商品/分类
  ├── /api/shop/c-endpoint/addresses/*→ user-product:8001   # 地址管理
  ├── /api/shop/c-endpoint/cart/*     → order-trade:8002    # 购物车
  ├── /api/shop/c-endpoint/orders/*   → order-trade:8002    # 订单
  ├── /api/shop/c-endpoint/logistics/*→ order-trade:8002    # 物流
  ├── /api/shop/c-endpoint/after-sales/*→ order-trade:8002  # 售后
  ├── /api/shop/b-endpoint/*          → admin:8003          # 管理后台
  ├── /api/ai/*                       → ai-service:8004     # AI 客服
  └── /*                              → frontend:5173       # 前端页面

后端内部通信（X-Internal-Token）：
  ai-service → user-product:8001/internal    # 用户/商品数据
  ai-service → order-trade:8002/internal     # 订单/物流/售后数据
```

---

## 物流系统

支付后动态推进，每 1 分钟追加一个新节点：

```
支付成功 → 📦 已揽件 @ 深圳仓库          (0分钟)
         → 🚚 运输中 @ 深圳集散中心       (1分钟)
         → 🚚 运输中 @ 广州中转           (2分钟)
         → 📬 派送中 @ 派送中             (3分钟)
         → ✅ 已签收 @ 您的手中           (5分钟)
```

- 调度器每 **30 秒**扫描未完成的物流记录
- 前端每 **15 秒**自动轮询刷新页面
- 隐藏未来节点，只展示已完成和当前节点

---

## 全链路测试

```bash
python tests/integration_test.py
```

**63 项测试全部通过 ✅**

| 测试模块 | 项数 | 覆盖内容 |
|----------|------|----------|
| 健康检查 | 4 | 4 个后端服务 |
| 用户认证 | 5 | 注册、重复注册、登录、错误密码、个人信息 |
| 地址管理 | 6 | 创建、列表、默认切换、删除 |
| 商品浏览 | 6 | 列表、搜索、热门、详情、分类树、404 |
| 购物车 | 7 | 添加、叠加、修改、超库存、删除 |
| 订单流程 | 11 | 创建、支付、状态刷新、重复支付、取消、物流、清空 |
| 售后 | 2 | 申请、列表 |
| 权限校验 | 3 | 无token、无效token、公开接口 |
| 管理后台 | 9 | 登录、分类、商品、订单、权限 |
| 内部接口 | 8 | 用户、商品、订单、物流、售后、令牌校验 |
| AI 客服 | 2 | 健康检查、对话接口 |

---

## 各模块 README 文档

- [👤 用户与商品服务](service-user-product/README.md) — 认证/商品/地址 API 详情
- [📦 购物车与交易服务](service-order-trade/README.md) — 购物车/订单/物流/定时任务
- [🛡️ 管理后台服务](service-admin/README.md) — 分类/商品/订单管理 + 缓存策略
- [🤖 AI 客服服务](ai-service/README.md) — 工具定义/环境变量/架构
- [🎨 前端](frontend/README.md) — 页面路由/设计系统/构建
- [📋 项目整合记录](integration.md) — 合并过程/修复记录/架构决策

---

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端框架 | Python FastAPI | 0.115 |
| 前端框架 | React + TypeScript + Vite | 19 / 6 |
| 数据库 | PostgreSQL + pgvector | 16 |
| 缓存 | Redis | 7 |
| 反向代理 | Nginx | latest |
| 容器化 | Docker Compose | 8 个容器 |
| LLM | LangChain + DeepSeek | — |
| 任务调度 | APScheduler | 3.11 |

## 设计主题

- 🎨 **白色** (#FFFFFF) + **翡翠绿** (#059669)
- 标题字体：**DM Serif Display**（衬线优雅）
- 正文字体：**DM Sans**（清晰现代）
- 点缀色：琥珀 (#F59E0B)、玫瑰 (#F43F5E)
