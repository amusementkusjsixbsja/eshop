# 项目整合记录

> 记录多分支合并过程中发现的问题、修复方案和架构决策，供后续参考。

## 一、分支合并策略

### 1.1 分支概览

| 分支 | 负责人 | 模块 | 状态 |
|------|--------|------|------|
| `feat/xiaob-user-product` | 小B | 用户认证 + 商品浏览 | 已合入 origin/master |
| `feat/xiaoc-order-trade` | 小C | 购物车 + 订单 + 物流 + 售后 | ✅ 合并（无冲突） |
| `feat/xiaod-admin` | 小D | 管理后台（分类/商品/订单） | ✅ 合并（无冲突） |
| `feat/xiaoa-ai-service` | 小A | AI 客服 | WIP 在工作目录 |
| `feat/xiaoa-frontend` | 小A | 前端页面 | WIP 在工作目录 |

### 1.2 合并顺序

```
git pull origin/master         # 先拉取已合入的小B代码（fast-forward）
git stash push -m "xiaoa-wip"  # 保护小A工作目录
git merge origin/feat/xiaoc-order-trade  # 合并小C
git merge origin/feat/xiaod-admin        # 合并小D
git stash pop                   # 恢复小A工作目录
```

### 1.3 冲突处理原则

冲突全部发生在小B的 `service-user-product/` 目录。处理策略：

```bash
# xiaoc-order-trade 合并时：
#   service-user-product/* → ours（保留 origin/master 中小B的实现）
#   service-order-trade/* → theirs（用小C实现）

# xiaod-admin 合并时：
#   service-admin/* → theirs（用小D实现）
#   service-user-product/* → ours（保留已有）
#   service-order-trade/* → ours（保留已有）
```

**关键发现**：origin/master 已有小B代码（通过 PR 合并→回退→重新合并），但 `user_service.py` 等 services 层文件因回退历史未被正确合入，导致 `internal_router.py` 引用了不存在的函数。修复方式：从 `origin/feat/xiaob-user-product` 分支 checkout 真实实现覆盖。

---

## 二、合并后修复的问题

### 2.1 baseURL 冲突

**问题**：小B将 `frontend/src/api/client.ts` 的 `baseURL` 从 `/api/shop` 改为 `http://localhost:8001`（直连 user-product）。

**影响**：所有非 user-product 的请求（购物车→order-trade:8002、管理后台→admin:8003）都会错误地发到 user-product。

**修复**：改回 `/api/shop`，由 Nginx 根据路径前缀路由到对应后端服务：

```
/api/shop/c-endpoint/auth/* → user-product:8001
/api/shop/c-endpoint/products/* → user-product:8001
/api/shop/c-endpoint/cart/* → order-trade:8002
/api/shop/c-endpoint/orders/* → order-trade:8002
/api/shop/c-endpoint/logistics/* → order-trade:8002
/api/shop/c-endpoint/after-sales/* → order-trade:8002
/api/shop/b-endpoint/* → admin:8003
/api/ai/* → ai-service:8004
/* → frontend:5173
```

### 2.2 前端 TypeScript 类型错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `ApiResponse` 缺少 `code`/`message` | 小A改为 AI 对话格式 | 恢复 `code`、`data`、`message` 字段 |
| `aiChat.ts` 类型断裂 | 类型定义变化 | 从 `ApiResponse<ChatResponse>` 改为直接 `ChatResponse` |
| `Order` 缺少 `user_id` | 管理后台需要 | 添加可选字段 `user_id?: number` |

### 2.3 支付后状态不刷新

**问题**：`pay_order()` 返回最小数据集（只有 id/status/paid_at），前端 `setOrder(res.data)` 后丢失商品明细、地址等信息。

**修复**：支付/取消操作后重新调用 `getOrderDetail()` 获取完整订单数据。

### 2.4 Vite 代理端口错误

**问题**：`vite.config.ts` 中 AI 服务代理指向 `localhost:8080`，实际运行在 `8004`。

**修复**：端口 8080 → 8004。

### 2.5 Nginx 路由缺失

**问题**：地址管理接口 `/c-endpoint/addresses` 没有 Nginx 路由规则，返回 500。

**修复**：在 `nginx.conf` 中添加对应 location。

### 2.6 order-trade 内部接口路径错误

**问题**：`internal_router.py` 同时定义了 `prefix="/internal"`，又在 `main.py` 以 `prefix="/internal"` 注册，导致真实路径为双重的 `/internal/internal/orders`。

**修复**：去掉 router 定义的 `prefix`，只保留 main.py 的注册前缀。

### 2.7 管理员密码错误

**问题**：init.sql 中的 bcrypt hash 是占位符，不是真实加密结果。

**修复**：用 `hash_password('admin123')` 生成真实 bcrypt hash 更新。

---

## 三、AI 客服身份识别改造

### 3.1 原有问题

- `chat_router.py` 中 `user_id = 1` 硬编码
- JWT 从未被解析，`authorization` 参数收到但不使用
- 工具调用不传 user_id，所有查询都针对 user_id=1
- LLM 不知道当前用户是谁

### 3.2 改造方案

**JWT 解码 → 获取用户上下文 → 注入 system prompt → 工具调用带 user_id**

```python
def _get_user_context(authorization):
    payload = extract_user_from_token(authorization)
    user_info = shop_client.get_user(payload["user_id"])
    payload["nickname"] = user_info["data"]["nickname"]
    return payload
```

**系统提示注入用户身份**：
```python
user_tag = f"""
## 当前用户
- 用户ID: {user_ctx['user_id']}
- 昵称: {user_ctx['nickname']}
- 邮箱: {user_ctx['email']}
"""
enhanced_prompt = SYSTEM_PROMPT + user_tag
```

### 3.3 工具调用链路

```
LLM 判断需要查订单
  → 返回 tool_call: get_orders
  → execute_tool("get_orders", {}, user_id=实际用户ID)
  → shop_client.get_orders(user_id)  → 调用 order-trade:8002/internal/orders
  → 结果回 LLM → 生成自然语言
```

新增 `get_user_info` 工具，让 AI 能主动查询和告知用户个人信息。

---

## 四、地址管理系统

### 4.1 数据库设计

```sql
CREATE TABLE shop.user_addresses (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES shop.users(id),
    label       VARCHAR(50) DEFAULT '',      -- 标签：家/公司/学校
    name        VARCHAR(100) NOT NULL,        -- 收货人
    phone       VARCHAR(20) NOT NULL,         -- 手机号
    address     TEXT NOT NULL,                -- 详细地址
    is_default  BOOLEAN DEFAULT FALSE,        -- 是否默认
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 后端 API

5 个端点：GET/POST/PUT/DELETE/PATCH（设为默认）。
默认地址互斥：设置一个地址为默认时，自动清除其他地址的默认标记。

### 4.3 购物车集成

购物车结算页面从弹窗输入地址改为卡片式地址选择器，支持：
- 展示已有地址列表，点选即用
- 默认地址自动选中
- 快捷跳转到地址管理页面

---

## 五、5 分钟极速物流系统

### 5.1 节点定义

```python
LOGISTICS_NODES = [
    (0,  "picked_up",       "深圳仓库"),
    (1,  "in_transit",      "深圳集散中心"),
    (2,  "in_transit",      "广州中转"),
    (3,  "out_for_delivery", "派送中"),
    (5,  "delivered",       "您的手中"),
]
```

### 5.2 推进机制

支付时创建物流记录，包含完整 5 分钟时间线。
APScheduler 每 **30 秒**扫描一次未送达的物流记录，根据已过分钟数计算应处节点，自动更新 `status` 和 `current_location`。

### 5.3 效果

用户支付后查看物流：
- 打开 → 已揽件
- 1 分钟后 → 运输中 @ 深圳集散中心
- 2 分钟后 → 运输中 @ 广州中转
- 3 分钟后 → 派送中
- 5 分钟后 → 已签收 ✅

---

## 六、测试体系

### 6.1 自动化集成测试

`tests/integration_test.py` — 覆盖 **63 项** 测试，通过率 **100%**：

| 模块 | 项数 | 内容 |
|------|------|------|
| 健康检查 | 4 | user-product, order-trade, admin, ai-service |
| 用户认证 | 5 | 注册、重复注册、登录、错误密码、个人信息 |
| 地址管理 | 6 | 创建、列表、默认切换、删除 |
| 商品浏览 | 6 | 列表、搜索、热门、详情、分类树、404 |
| 购物车 | 7 | 查看、添加、叠加、修改、超库存、删除 |
| 订单流程 | 11 | 创建、支付、状态刷新、重复支付、取消、物流、清空 |
| 售后 | 2 | 申请、列表 |
| 权限校验 | 3 | 无token、无效token、公开接口 |
| 管理后台 | 9 | 登录、角色、分类、商品、订单、筛选、权限 |
| 内部接口 | 8 | 用户、商品、订单、物流、售后、令牌校验 |
| AI 客服 | 2 | 健康检查、对话接口 |

### 6.2 测试通过率趋势

```
第1次: 49/56 → 87.5%  （内部接口404、管理员密码）
第2次: 63/63 → 100% ✅ （全部修复）
```

---

## 七、架构决策记录

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 前端 baseURL | /api/shop vs localhost:8001 | `/api/shop` | Nginx 统一路由，避免跨服务调用错误 |
| AI 客户端模式 | Mock vs 真实 | 真实（MOCK_MODE=false） | 生产环境必须从数据库获取数据 |
| AI 内部接口 | 单URL vs 双URL | 双URL | user-product 和 order-trade 分属不同服务 |
| 地址存储 | 单字段JSON vs 独立表 | 独立表 | 支持 CRUD、默认地址、标签管理 |
| 物流时间线 | 静态 vs 动态推进 | 动态推进 | 让演示/开发更直观看到物流变化 |
| 前端样式 | inline vs CSS变量 | CSS变量 | 统一主题，支持响应式 |
| Docker构建 | 缓存 vs 无缓存 | 缓存（除非新文件） | 加快构建速度 |

---

## 八、已知待办

- [ ] `conversation_service.py` 使用内存存储，重启丢失。可改用 Redis 或 PostgreSQL 持久化
- [ ] AI 客服需要配置 `LLM_API_KEY` 和 `LLM_API_URL` 环境变量
- [ ] Docker 中没有 `.env` 文件示例的 AI 服务配置（需自行创建）
- [ ] 超时取消订单的阈值（当前 5 分钟）偏短，可调整
