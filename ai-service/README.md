# AI 客服服务

基于 LangChain + DeepSeek 的智能客服助手，支持 Function Calling 工具调用和流式 SSE 输出。

## 当前状态

- ✅ **JWT 用户身份识别** — 解码前端传来的 JWT，提取 user_id/email/role
- ✅ **真实数据查询** — 通过内部接口调用 user-product 和 order-trade 获取实时业务数据
- ✅ **Function Calling** — LLM 自主判断用户意图，调用订单/物流/售后/商品工具
- ✅ **流式 SSE 输出** — 逐 token 流式返回，实时打字效果
- ✅ **对话记忆** — 内存存储对话历史，支持多轮上下文
- ✅ **用户上下文注入** — LLM 知道当前用户是谁（昵称、邮箱、角色）
- ✅ **get_user_info 工具** — AI 可以查询和告知用户个人信息

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | 非流式对话（工具调用 → 完整回复） |
| POST | `/api/ai/chat/stream` | 流式 SSE 对话（逐 token 输出） |
| GET | `/health` | 健康检查 |

认证方式：`Authorization: Bearer <user_jwt>`

## 架构

```
用户提问（带 JWT）
  │
  ▼
chat_router.py  ←─── conversation_service.py（对话记忆）
  │  ├─ JWT 解码 → user_id / email / nickname
  │  └─ 注入用户上下文到 system prompt
  │
  ▼
chat_with_llm() + TOOL_DEFINITIONS
  │
  ├─ LLM 直接回复 → 返回给用户
  └─ LLM 要求调用工具
       │
       ▼
     execute_tool(user_id) → shop_client.py（调用内部接口）→ 结果回 LLM → 最终回复
```

## 工具列表

| 工具名 | 说明 | 数据源 |
|--------|------|--------|
| `get_user_info` | 查询当前用户信息 | user-product:8001 |
| `get_orders` | 查询订单列表 | order-trade:8002 |
| `get_order_detail` | 查询订单详情 | order-trade:8002 |
| `get_logistics` | 查询物流进度 | order-trade:8002 |
| `get_after_sales` | 查询售后记录 | order-trade:8002 |
| `search_products` | 搜索商品 | user-product:8001 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | — | DeepSeek API Key |
| `LLM_API_URL` | — | DeepSeek API URL |
| `MOCK_MODE` | `false` | 是否使用 Mock 数据 |
| `USER_INTERNAL_URL` | `http://user-product:8001/internal` | 用户/商品内部接口 |
| `ORDER_INTERNAL_URL` | `http://order-trade:8002/internal` | 订单/物流/售后内部接口 |
| `INTERNAL_API_TOKEN` | `dev-internal-token` | 内部接口认证令牌 |

## 启动方式

```bash
pip install -r requirements.txt
# 配置 .env（LLM_API_KEY, LLM_API_URL）
uvicorn main:app --reload --port 8004
```

Swagger 文档：`http://localhost:8004/docs`
