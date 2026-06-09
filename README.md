# 电商平台 (E-Shop)

基于 Python FastAPI + React 的轻量级电商平台 Demo。支持用户注册登录、商品浏览、购物车、下单支付、物流追踪、售后管理、AI 智能客服和管理后台。

## 项目结构

| 模块 | 目录 | 技术栈 | 端口 |
|------|------|--------|------|
| 用户与商品 | `service-user-product/` | Python FastAPI + PostgreSQL | 8001 |
| 购物车与交易 | `service-order-trade/` | Python FastAPI + PostgreSQL + APScheduler | 8002 |
| 管理后台 | `service-admin/` | Python FastAPI + PostgreSQL | 8003 |
| AI 客服 | `ai-service/` | Python FastAPI + LangChain + DeepSeek | 8004 |
| 前端 | `frontend/` | React 19 + Vite + TypeScript | 5173 |
| 共享库 | `shared/` | Python 基础库（DB/Redis/JWT） | — |
| 基础设施 | `docker/` | Docker Compose + Nginx + init.sql | 80 |

## 快速启动

```bash
# 启动全部服务
docker compose -f docker/docker-compose.yml up -d

# 查看状态
docker compose -f docker/docker-compose.yml ps
```

访问 `http://localhost:80`（Nginx 统一入口）
前端开发服务器：`cd frontend && npm install && npm run dev`（端口 5173）

## 预置账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@shop.local | admin123 |
| 普通用户 | user@test.com | 123456 |

## 架构图

```
用户 → Nginx (:80)
  ├── /api/shop/c-endpoint/* → user-product:8001（认证/商品/地址）
  ├── /api/shop/c-endpoint/* → order-trade:8002（购物车/订单/物流/售后）
  ├── /api/shop/b-endpoint/* → admin:8003（管理后台）
  ├── /api/ai/* → ai-service:8004（AI 客服）
  └── /* → frontend:5173（前端页面）

后端内部通信（X-Internal-Token）：
  ai-service → user-product:8001/internal（用户/商品）
  ai-service → order-trade:8002/internal（订单/物流/售后）
```

## 各模块 README

- [用户与商品服务](service-user-product/README.md)
- [购物车与交易服务](service-order-trade/README.md)
- [管理后台服务](service-admin/README.md)
- [AI 客服服务](ai-service/README.md)
- [前端](frontend/README.md)

## 全链路测试

```bash
python tests/integration_test.py
```

覆盖 63 项测试：健康检查、用户认证、地址管理、商品浏览、购物车、订单流程、售后、权限校验、管理后台、内部接口、AI 客服。

## 技术栈

- **后端**：Python 3.10 + FastAPI 0.115
- **前端**：React 19 + TypeScript + Vite 6
- **数据库**：PostgreSQL 16 + pgvector
- **缓存**：Redis 7
- **代理**：Nginx
- **容器**：Docker Compose（8 个容器）

## 设计主题

- 白色 (#FFFFFF) + 翡翠绿 (#059669) 主题
- 标题字体：DM Serif Display
- 正文字体：DM Sans
- 点缀色：琥珀 (#F59E0B)、玫瑰 (#F43F5E)
