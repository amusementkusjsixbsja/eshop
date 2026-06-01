# 小A 开发指南 — 前端 + AI 服务 + DevOps

## 你的文件夹

| 文件夹 | 内容 | 技术栈 |
|--------|------|--------|
| `frontend/` | 全部前端页面 | React 19 + Vite + TypeScript |
| `ai-service/` | AI 客服后端服务 | Python FastAPI |
| `docker/` | Nginx 配置（nginx.conf） | 可调整路由规则 |

> 注意：`docker/` 下的 `docker-compose.yml` 和 `init.sql` 你在联调阶段可能需要调整，但初期不动。

## 你的任务

### 1. 前端 — 页面列表

| 页面 | 路由 | 状态 |
|------|------|------|
| 登录 | `/login` | 基本可用 |
| 注册 | `/register` | 基本可用 |
| 商品列表 | `/products` | 基本可用 |
| 商品详情 | `/products/:id` | 基本可用 |
| 购物车 | `/cart` | 基本可用 |
| 订单列表 | `/orders` | 基本可用 |
| 订单详情 | `/orders/:id` | 基本可用 |
| 物流追踪 | `/logistics/:orderId` | 基本可用 |
| 售后中心 | `/after-sales` | 基本可用 |
| 分类管理 | `/admin/categories` | 基本可用 |
| 商品管理 | `/admin/products` | 基本可用 |
| 订单管理 | `/admin/orders` | 基本可用 |
| AI 客服浮窗 | 全局组件 | 基本可用 |

**当前状态：** 所有页面有基本功能骨架，需要你打磨 UI、完善交互。

### 2. AI 客服服务

`ai-service/` 已有完整骨架：

- `routers/chat_router.py` — 对话路由 + 意图识别 + FAQ + 模板回复
- `clients/shop_client.py` — 调用后端内部接口的客户端
- `utils/auth.py` — JWT 解码
- `services/llm_service.py` — LLM 集成占位
- `services/faq_service.py` — pgvector FAQ 检索占位

**当前状态：** 关键词匹配的对话，可直接运行。你可以：
1. 集成真实 LLM（OpenAI/Claude API）
2. 升级意图识别为 LLM 分类
3. 实现 pgvector FAQ 向量检索
4. 完善对话体验

### 3. DevOps

- `docker/nginx/nginx.conf` — 如需修改路由规则
- 联调阶段确保全链路通畅

## 启动方式

```bash
# 启动 AI 服务 + 前端 + 基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis ai-service frontend

# 访问前端 http://localhost（通过 Nginx）
# 如需热重载，在本地另开终端运行：
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173（热重载模式）
```

## 接口对接

前端所有 API 调用通过 `src/api/*.ts` 封装，对照接口契约：

- `api/client.ts` — axios 实例（自动附加 JWT Token + 统一错误处理）
- `api/auth.ts` — 登录/注册/个人信息
- `api/product.ts` — 商品列表/详情/分类树
- `api/cart.ts` — 购物车
- `api/order.ts` — 订单
- `api/logistics.ts` — 物流
- `api/afterSale.ts` — 售后
- `api/admin.ts` — 管理后台
- `api/aiChat.ts` — AI 对话

**类型定义全部在 `src/types/index.ts`**，与接口契约一一对应。

## 前后端联调

1. 后端各服务已有 mock 数据返回，前端可直接对接
2. 当后端同学替换为真实数据库查询后，前端不需要改任何代码
3. 联调时只需要确保 Nginx 路由正确、API 返回格式一致
