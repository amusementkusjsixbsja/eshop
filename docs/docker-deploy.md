# Docker 部署与开发指南

## 一、完整部署（全栈启动）

```bash
# 进入项目根目录
cd /path/to/eshop

# 复制环境变量配置
cp docker/.env.example docker/.env

# 构建并启动全部 7 个容器
docker compose -f docker/docker-compose.yml up -d

# 查看所有服务状态
docker compose -f docker/docker-compose.yml ps

# 查看日志
docker compose -f docker/docker-compose.yml logs -f

# 只查看某个服务的日志
docker compose -f docker/docker-compose.yml logs -f user-product
```

**启动后的容器：**

| 容器名 | 端口 | 访问方式 |
|--------|------|---------|
| nginx | :80 | **http://localhost**（统一入口，含前端页面）|
| frontend | — | 通过 nginx (localhost:80) 访问 |
| user-product | :8001 | 小B http://localhost:8001/health |
| order-trade | :8002 | 小C http://localhost:8002/health |
| admin | :8003 | 小D http://localhost:8003/health |
| ai-service | :8004 | 小A http://localhost:8004/health |
| postgres | — | 内部连接（容器名 postgres:5432）|
| redis | :6379 | 内部连接 |

## 二、个人独立开发（只跑自己的 + 基础设施）

**每个人使用同一份 docker-compose.yml，但只启动需要的服务。**

```bash
# ★ 小B：只启动自己的服务 + 数据库 + 缓存
docker compose -f docker/docker-compose.yml up -d postgres redis user-product

# ★ 小C：只启动自己的服务 + 数据库 + 缓存
docker compose -f docker/docker-compose.yml up -d postgres redis order-trade

# ★ 小D：只启动自己的服务 + 数据库 + 缓存
docker compose -f docker/docker-compose.yml up -d postgres redis admin

# ★ 小A：启动 AI 服务 + 前端 + 基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis ai-service frontend

# ★ 全栈联调：全部启动
docker compose -f docker/docker-compose.yml up -d
```

### 为什么自己启动不会报错？

每个后端服务**独立直连数据库**，不依赖其他后端服务的 HTTP API：

```
user-product → PostgreSQL（查 shop.products）+ Redis（缓存）
order-trade  → PostgreSQL（查 shop.orders）+ Redis（缓存）
admin        → PostgreSQL（查 shop.products）+ Redis（缓存）
ai-service   → 调用 user-product 和 order-trade 的 HTTP 接口
```

- init.sql 在 postgres 首次启动时创建了所有表
- 每个服务只操作用到的表，其他服务是否存在不影响
- **唯一例外**：AI 服务需要调用后端内部接口，如果后端没启动则降级为纯 FAQ 回答

## 三、前后端联调模式

```bash
# 终端 1：启动所有后端服务
docker compose -f docker/docker-compose.yml up -d

# 终端 2：启动前端开发服务器（热重载）
cd frontend
npm install      # 首次需要
npm run dev      # http://localhost:5173
```

前端 Vite 配置了代理规则（`vite.config.ts`），
`/api/shop/*` → `http://localhost:80`（Nginx）
`/api/ai/*`   → `http://localhost:80`（Nginx）

## 四、数据库操作

```bash
# 进入 PostgreSQL 命令行
docker compose -f docker/docker-compose.yml exec postgres psql -U user -d agent

# 常用命令
\dt shop.*        # 查看所有电商表
SELECT * FROM shop.users;  # 查询用户
SELECT * FROM shop.products;  # 查询商品

# 重置数据库（删除所有数据重新初始化）
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

## 五、常用命令速查

| 命令 | 说明 |
|------|------|
| `docker compose up -d` | 启动所有服务 |
| `docker compose down` | 停止所有服务（保留数据） |
| `docker compose down -v` | 停止所有服务（**删除数据**） |
| `docker compose logs -f [服务名]` | 查看实时日志 |
| `docker compose ps` | 查看服务状态 |
| `docker compose restart [服务名]` | 重启单个服务 |
| `docker compose build [服务名]` | 重新构建镜像 |

## 六、常见问题

### Q: 端口被占用怎么办？
A: 修改 `docker-compose.yml` 中对应服务的 `ports` 映射，如 `"8001:8001"` 改为 `"8005:8001"`。

### Q: 改了代码但 Docker 没更新？
A: 需要重新构建镜像：
```bash
docker compose -f docker/docker-compose.yml build user-product
docker compose -f docker/docker-compose.yml up -d user-product
```

### Q: 数据库数据没了？
A: 如果执行了 `docker compose down -v`，数据卷会被删除。之后 `up -d` 时会重新执行 init.sql。

### Q: 如何单独调试某个 API？
A: 使用 curl 或 Postman：
```bash
# 测试商品列表（经过 Nginx）
curl http://localhost/api/shop/c-endpoint/products

# 测试内部接口（直接访问服务，不经过 Nginx）
curl http://localhost:8001/internal/products/search?keyword=门锁 \
  -H "X-Internal-Token: dev-internal-token"
```
