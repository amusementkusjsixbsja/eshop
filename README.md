# 电商平台 (E-Shop)

基于 Python FastAPI + React 的轻量级电商平台 Demo。

## 项目结构

| 目录 | 说明 | 负责人 |
|------|------|--------|
| `frontend/` | React + Vite + TypeScript 前端 | 小A |
| `ai-service/` | Python FastAPI AI 客服服务 | 小A |
| `service-user-product/` | 用户认证 + 商品浏览 + 分类树 | 小B |
| `service-order-trade/` | 购物车 + 订单 + 物流 + 售后 | 小C |
| `service-admin/` | 管理后台（分类/商品/订单管理） | 小D |
| `shared/` | 共享 Python 基础设施库 | 框架 |
| `docker/` | Docker Compose + Nginx + init.sql | 小A维护 |

## 快速启动

```bash
# 1. 复制环境变量
cp docker/.env.example docker/.env

# 2. 启动全部服务
docker compose -f docker/docker-compose.yml up -d

# 3. 查看状态
docker compose -f docker/docker-compose.yml ps
```

访问 `http://localhost:80`（Nginx 统一入口）
前端开发服务器：`cd frontend && npm install && npm run dev`（端口 5173）

## 预置账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@shop.local | admin123 |
| 普通用户 | user@test.com | 123456 |

## 各人开发指南

- [Git 工作流程](docs/git-workflow.md)
- [Docker 部署文档](docs/docker-deploy.md)
- [小A 开发指南](docs/dev-guide-xiaoa.md)
- [小B 开发指南](docs/dev-guide-xiaob.md)
- [小C 开发指南](docs/dev-guide-xiaoc.md)
- [小D 开发指南](docs/dev-guide-xiaod.md)

## 技术栈

- 后端：Python 3.10.10 + FastAPI
- 前端：React 19 + Vite + TypeScript
- 数据库：PostgreSQL 16 + pgvector
- 缓存：Redis 7.x
- 反向代理：Nginx
- 容器化：Docker Compose（6 个容器）
