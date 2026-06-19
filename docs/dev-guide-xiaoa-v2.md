# 🅰️ 小A — 第二轮开发指南：AI 客服增强 + 前端全功能

> **分支：** `feat/xiaoa-ai-service` + `feat/xiaoa-frontend`
> **服务：** `ai-service`（端口 8004）+ `frontend`（端口 5173）
> **依赖：** 小C 的内部下单端点 + 小B 的评价内部接口
> **预计工作量：** AI 服务 8 个文件 + 前端 9 个文件 = 17 个文件（最大工作量）

---

## 一、任务总览

### AI 服务（ai-service）

| 序号 | 文件 | 操作 | 说明 |
|:----:|------|:----:|------|
| 1 | `ai-service/services/tools.py` | 修改 | 新增 3 个工具定义 + 分发逻辑 |
| 2 | `ai-service/clients/shop_client.py` | 修改 | 新增 4 个方法 + `_post()` 方法 |
| 3 | `ai-service/services/faq_service.py` | 重写 | 完整 FAQ 向量检索实现 |
| 4 | `ai-service/services/database.py` | ✅ 新建 | 数据库连接池 |
| 5 | `ai-service/services/conversation_service.py` | 重写 | 从内存存储迁移到数据库持久化 |
| 6 | `ai-service/services/llm_service.py` | 修改 | 更新 SYSTEM_PROMPT |
| 7 | `ai-service/routers/chat_router.py` | 修改 | 集成 FAQ 检索步骤 |
| 8 | `ai-service/requirements.txt` | 修改 | 新增 psycopg2-binary |

### 前端（frontend）

| 序号 | 文件 | 操作 | 说明 |
|:----:|------|:----:|------|
| 9 | `frontend/src/api/review.ts` | ✅ 新建 | 评价 API 函数 |
| 10 | `frontend/src/types/index.ts` | 修改 | 新增 Review、ReviewStats 等类型 |
| 11 | `frontend/src/components/StarRating.tsx` | ✅ 新建 | 星级评分组件 |
| 12 | `frontend/src/components/ReviewForm.tsx` | ✅ 新建 | 评价表单组件 |
| 13 | `frontend/src/pages/product/ProductDetailPage.tsx` | 修改 | 添加评价区域 |
| 14 | `frontend/src/pages/order/OrderDetailPage.tsx` | 修改 | 添加评价入口 + 支付方式选择 |
| 15 | `frontend/src/api/order.ts` | 修改 | payOrder 增加 payment_method 参数 |
| 16 | `frontend/src/components/ChatPopup.tsx` | 修改 | 订单卡片 + 支付按钮 + 评价总结 |
| 17 | `frontend/src/components/ChatPopup.css` | 修改 | 新增样式 |

---

## 二、开发顺序建议

基于依赖关系，建议按以下顺序开发：

```
Phase 1（独立）:  database.py → conversation_service.py → faq_service.py
Phase 2（独立）:  requirements.txt → 前端类型定义 → StarRating组件
Phase 3（依赖小C）: shop_client.py → tools.py
Phase 4（依赖小B小C）: llm_service.py → chat_router.py → 前端集成
```

---

## 三、AI 服务详细实现

### Step 1：创建 `services/database.py`

ai-service 当前不直接连数据库。新增数据库连接池，复用 `shop_shared` 的模式但独立实现（因为 ai-service 不依赖 shop_shared 的包结构）。

```python
"""ai-service 数据库连接池。

供 FAQ 检索和对话持久化使用。
连接 customer_service schema 所在的 PostgreSQL 数据库。
"""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:1234@postgres:5432/agent")

# 简单连接池（生产环境建议用 psycopg2.pool.ThreadedConnectionPool）
_conn = None


def get_connection():
    """获取数据库连接（懒加载）。"""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(DATABASE_URL)
        _conn.autocommit = True
    return _conn


@contextmanager
def get_cursor():
    """获取数据库游标（上下文管理器）。"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()


def close_connection():
    """关闭数据库连接。"""
    global _conn
    if _conn and not _conn.closed:
        _conn.close()
    _conn = None
```

---

### Step 2：重写 `services/conversation_service.py`

从内存 dict 存储迁移到 `customer_service.conversations` 和 `messages` 表：

```python
"""对话持久化服务（数据库版）。

操作 customer_service.conversations 和 messages 表。
"""

import uuid
from datetime import datetime

from services.database import get_cursor


def create_conversation(user_id: str) -> str:
    """创建新对话，返回 UUID。"""
    conv_id = str(uuid.uuid4())
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO customer_service.conversations (id, user_id, title)
            VALUES (%s, %s, %s)
        """, (conv_id, user_id, f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    return conv_id


def add_message(conv_id: str, role: str, content: str, turn_number: int = None, metadata: dict = None):
    """添加消息到对话。

    role: 'user' / 'assistant' / 'system'
    """
    import json
    if turn_number is None:
        # 自动计算 turn_number
        with get_cursor() as cur:
            cur.execute("""
                SELECT COALESCE(MAX(turn_number), 0) + 1 as next_turn
                FROM customer_service.messages
                WHERE conversation_id = %s
            """, (conv_id,))
            turn_number = cur.fetchone()["next_turn"]

    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO customer_service.messages
                (conversation_id, role, content, turn_number, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """, (conv_id, role, content, turn_number, json.dumps(metadata) if metadata else None))

        # 更新对话的 updated_at
        cur.execute("""
            UPDATE customer_service.conversations
            SET updated_at = NOW()
            WHERE id = %s
        """, (conv_id,))


def get_history(conv_id: str) -> list[dict]:
    """获取对话历史（按 turn_number 升序）。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT role, content, turn_number, metadata, created_at
            FROM customer_service.messages
            WHERE conversation_id = %s
            ORDER BY turn_number ASC
        """, (conv_id,))
        return [dict(row) for row in cur.fetchall()]


def update_conversation_title(conv_id: str, title: str):
    """更新对话标题。"""
    with get_cursor() as cur:
        cur.execute("""
            UPDATE customer_service.conversations
            SET title = %s, updated_at = NOW()
            WHERE id = %s
        """, (title, conv_id))
```

---

### Step 3：重写 `services/faq_service.py`

```python
"""RAG FAQ 检索服务。

流程：用户提问 → 生成 embedding → pgvector 余弦相似度查询 → 返回最佳匹配答案
"""

import os
import requests

from services.database import get_cursor

# Embedding 配置
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-v3"  # 通义千问 embedding 模型
EMBEDDING_DIMENSION = 1024
FAQ_MATCH_THRESHOLD = 0.85


def generate_embedding(text: str) -> list[float]:
    """调用 LLM API 生成 1024 维 embedding 向量。"""
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY 未配置，无法生成 embedding")

    resp = requests.post(
        f"{LLM_API_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
            "dimensions": EMBEDDING_DIMENSION,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def search_faq(query: str, threshold: float = FAQ_MATCH_THRESHOLD) -> str | None:
    """FAQ 向量检索。

    Args:
        query: 用户提问文本
        threshold: 相似度阈值（默认 0.85）

    Returns:
        匹配的答案字符串，无匹配返回 None
    """
    try:
        embedding = generate_embedding(query)
    except Exception as e:
        # embedding 生成失败时静默降级
        return None

    with get_cursor() as cur:
        cur.execute("""
            SELECT question, answer,
                   1 - (embedding <=> %s::vector) as similarity
            FROM customer_service.faq_embeddings
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 1
        """, (embedding, embedding))
        row = cur.fetchone()

    if row and row["similarity"] >= threshold:
        return row["answer"]
    return None


def add_faq(question: str, answer: str, category: str = "general") -> int:
    """添加 FAQ 条目并生成 embedding。"""
    import json

    embedding = generate_embedding(question + " " + answer)
    metadata = json.dumps({"category": category})

    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO customer_service.faq_embeddings (question, answer, embedding, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (question, answer, embedding, metadata))
        return cur.fetchone()["id"]
```

---

### Step 4：修改 `clients/shop_client.py`

#### 4a. 新增 `_post()` 方法

```python
def _post(self, base_url: str, path: str, body: dict = None) -> dict:
    """发送 POST 请求到内部服务。"""
    try:
        url = f"{base_url}{path}"
        r = self._client.post(url, json=body, headers=self._headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"code": -1, "data": {}, "message": f"电商服务不可用: {e}"}
```

#### 4b. 新增业务方法

```python
# ─── 对话下单（v2.0）───

def create_order(self, user_id: int, items: list, address: str) -> dict:
    """AI 对话下单：调用 order-trade 内部接口。"""
    return self._post(ORDER_INTERNAL_URL, "/orders/create", {
        "user_id": user_id,
        "items": items,
        "address": address,
    })


# ─── 支付（v2.0）───

def pay_order(self, order_id: int, user_id: int, payment_method: str = "wechat") -> dict:
    """执行支付：调用 order-trade 支付端点。"""
    return self._post(ORDER_INTERNAL_URL, f"/orders/{order_id}/pay", {
        "payment_method": payment_method,
    })


# ─── 商品评价（v2.0）───

def get_product_reviews(self, product_id: int) -> dict:
    """获取商品评价和统计。"""
    return self._get(USER_INTERNAL_URL, f"/reviews/product/{product_id}")

def get_product_review_stats(self, product_id: int) -> dict:
    """获取商品评价统计。"""
    return self._get(USER_INTERNAL_URL, f"/reviews/product/{product_id}/stats")
```

---

### Step 5：修改 `services/tools.py`

#### 5a. 在 `TOOL_DEFINITIONS` 末尾追加 3 个新工具

```python
# 7. create_order — 对话下单
{
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "为用户创建订单。请在多轮对话中确认商品、数量、收货地址后，经用户最终确认才能调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "商品 ID"},
                            "quantity": {"type": "integer", "description": "数量"}
                        },
                        "required": ["product_id", "quantity"]
                    },
                    "description": "商品列表，每项包含商品 ID 和数量"
                },
                "address": {"type": "string", "description": "收货地址完整文本"}
            },
            "required": ["items", "address"]
        }
    }
},

# 8. pay_order — 执行支付
{
    "type": "function",
    "function": {
        "name": "pay_order",
        "description": "为订单执行支付。请在用户确认支付后调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "订单 ID"},
                "payment_method": {
                    "type": "string",
                    "enum": ["wechat", "alipay", "card", "balance"],
                    "description": "支付方式：微信/支付宝/银行卡/余额"
                }
            },
            "required": ["order_id"]
        }
    }
},

# 9. get_product_reviews — 获取商品评价
{
    "type": "function",
    "function": {
        "name": "get_product_reviews",
        "description": "获取某商品的用户评价和评分统计。用户询问商品口碑、质量、使用体验时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "商品 ID"},
                "product_name": {"type": "string", "description": "商品名称（便于AI引用）"}
            },
            "required": ["product_id"]
        }
    }
},
```

#### 5b. 在 `TOOL_MAP` 中注册

```python
TOOL_MAP = {
    # ... 原有 6 个 ...
    "create_order": shop_client.create_order,
    "pay_order": shop_client.pay_order,
    "get_product_reviews": shop_client.get_product_reviews,
}
```

#### 5c. 在 `execute_tool()` 中为 `create_order` 和 `pay_order` 注入 user_id

注意：`create_order` 和 `pay_order` 需要 `user_id`（从 JWT 获取，不是 LLM 提供的）。

```python
def execute_tool(name: str, arguments: dict, user_id: int) -> str:
    # ... 原有逻辑 ...
    # 对于需要 user_id 的工具，注入参数
    if name in ("create_order", "pay_order"):
        arguments["user_id"] = user_id
    # ... 原有执行逻辑 ...
```

---

### Step 6：更新 `services/llm_service.py` — SYSTEM_PROMPT

在现有 SYSTEM_PROMPT 末尾追加能力说明：

```
## 新增能力（v2.0）

### 对话下单
- 你可以帮助用户通过对话完成下单
- 流程：搜索商品 → 展示给用户 → 确认商品和数量 → 确认收货地址 → 用户确认后调用 create_order
- ⚠️ 必须经过用户最终确认才能调用 create_order
- 下单前必须检查库存（通过 search_products 查看 stock 字段）
- 地址优先使用用户的默认地址

### 支付
- 用户确认支付后，调用 pay_order 执行支付
- 支持的支付方式：微信(wechat)、支付宝(alipay)、银行卡(card)、余额(balance)
- 支付前请让用户选择支付方式

### 商品评价分析
- 用户询问商品口碑时，调用 get_product_reviews 获取评价数据
- 根据评价数据总结优缺点，用简洁的要点形式展示
- 可结合评分分布和具体评价内容给出购买建议

### 平台政策问答
- 平台政策类问题（退货、物流、支付等），可以直接利用 FAQ 知识库回答
- 如果你的知识库中有相关信息，优先使用
```

---

### Step 7：修改 `routers/chat_router.py` — 集成 FAQ 检索

在 `_resolve_tool_calls()` 之前插入 FAQ 检查逻辑：

#### 7a. 在 `chat_router.py` 顶部导入 faq_service

```python
from services.faq_service import search_faq
```

#### 7b. 在 `_resolve_tool_calls()` 之前新增 FAQ 检索步骤

找到 `POST /chat` 端点的主逻辑，修改为：

```python
@router.post("/chat")
def chat(req: ChatRequest, user=Depends(get_current_user)):
    user_ctx = _get_user_context(user)

    # 创建/恢复对话
    conv_id = req.conversation_id or create_conversation(str(user["id"]))

    # 1. ✅ FAQ 优先检索
    faq_answer = search_faq(req.question)
    if faq_answer:
        # FAQ 匹配命中，直接返回
        add_message(conv_id, "user", req.question)
        add_message(conv_id, "assistant", faq_answer)
        return ChatResponse(answer=faq_answer, conversation_id=conv_id)

    # 2. 进入 LLM 工具调用流程
    messages = _build_messages(req.question, conv_id, user_ctx)
    answer = _resolve_tool_calls(messages, user_id=user["id"])

    # 保存对话
    add_message(conv_id, "user", req.question)
    add_message(conv_id, "assistant", answer)

    return ChatResponse(answer=answer, conversation_id=conv_id)
```

同样的逻辑应用到流式端点：

```python
@router.post("/chat/stream")
def chat_stream(req: ChatRequest, user=Depends(get_current_user)):
    user_ctx = _get_user_context(user)
    conv_id = req.conversation_id or create_conversation(str(user["id"]))

    # 1. ✅ FAQ 优先检索
    faq_answer = search_faq(req.question)
    if faq_answer:
        add_message(conv_id, "user", req.question)
        add_message(conv_id, "assistant", faq_answer)
        return StreamingResponse(
            _event_stream_faq(faq_answer, conv_id),
            media_type="text/event-stream",
        )

    # 2. 原有流式逻辑...
    # ...
```

新增辅助函数：

```python
def _event_stream_faq(answer: str, conv_id: str):
    """FAQ 命中的流式输出（直接返回完整答案）。"""
    yield f"data: {json.dumps({'type': 'token', 'content': answer})}\n\n"
    yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id})}\n\n"
    yield "data: [DONE]\n\n"
```

---

### Step 8：修改 `requirements.txt`

```txt
# 新增（v2.0）
psycopg2-binary>=2.9.9
```

---

## 四、前端详细实现

### Step 9：前端类型定义 — `types/index.ts`

追加以下类型：

```typescript
// ── 评价系统（v2.0） ──

export interface Review {
  id: number;
  product_id: number;
  user_id: number;
  nickname?: string;
  order_id: number;
  rating: number;
  content: string;
  status: 'visible' | 'hidden';
  created_at: string;
  updated_at?: string;
}

export interface ReviewStats {
  avg_rating: number;
  total_count: number;
  distribution: { [key: number]: number };  // {1: 2, 2: 5, 3: 15, 4: 45, 5: 58}
}

// ── 支付增强（v2.0） ──

export type PaymentMethod = 'wechat' | 'alipay' | 'card' | 'balance' | 'mock';

export interface PaymentRecord {
  id: number;
  order_id: number;
  amount: number;
  method: PaymentMethod;
  status: 'processing' | 'success' | 'failed';
  transaction_no: string;
  finished_at?: string;
  error_message?: string;
  created_at: string;
}

// ── AI 对话下单（v2.0） ──

export interface OrderItemInput {
  product_id: number;
  quantity: number;
}

export interface CreateOrderResult {
  id: number;
  total_amount: number;
  status: string;
  items: OrderItem[];
}
```

### Step 10：评价 API — `api/review.ts`

```typescript
import { client } from './client';
import type { ApiResponse, Review, ReviewStats, PaginatedData } from '../types';

export async function createReview(data: {
  product_id: number;
  order_id: number;
  rating: number;
  content: string;
}): Promise<ApiResponse<Review>> {
  return client.post('/c-endpoint/reviews', data);
}

export async function getProductReviews(
  productId: number,
  page: number = 1,
  size: number = 10
): Promise<ApiResponse<PaginatedData<Review>>> {
  return client.get(`/c-endpoint/reviews/product/${productId}`, {
    params: { page, size },
  });
}

export async function getProductReviewStats(
  productId: number
): Promise<ApiResponse<ReviewStats>> {
  return client.get(`/c-endpoint/reviews/product/${productId}/stats`);
}

export async function getUserReviews(): Promise<ApiResponse<Review[]>> {
  return client.get('/c-endpoint/reviews/user/me');
}
```

### Step 11：星级评分组件 — `components/StarRating.tsx`

```tsx
import React from 'react';

interface StarRatingProps {
  rating: number;
  maxRating?: number;
  size?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onChange?: (rating: number) => void;
  showValue?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  maxRating = 5,
  size = 'md',
  interactive = false,
  onChange,
  showValue = false,
}) => {
  const [hoverRating, setHoverRating] = React.useState(0);
  const displayRating = hoverRating || rating;

  const sizeMap = { sm: '16px', md: '20px', lg: '28px' };
  const starSize = sizeMap[size];

  const stars = [];
  for (let i = 1; i <= maxRating; i++) {
    const filled = i <= displayRating;
    const halfFilled = !filled && i - 0.5 <= displayRating;

    stars.push(
      <span
        key={i}
        style={{
          cursor: interactive ? 'pointer' : 'default',
          fontSize: starSize,
          color: filled ? '#f59e0b' : halfFilled ? '#fcd34d' : '#d1d5db',
          transition: 'color 0.15s',
          userSelect: 'none',
        }}
        onClick={() => interactive && onChange?.(i)}
        onMouseEnter={() => interactive && setHoverRating(i)}
        onMouseLeave={() => interactive && setHoverRating(0)}
        role={interactive ? 'button' : 'img'}
        aria-label={`${i} 星`}
      >
        ★
      </span>
    );
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      {stars}
      {showValue && (
        <span style={{ marginLeft: '4px', fontSize: starSize, color: '#6b7280' }}>
          {rating.toFixed(1)}
        </span>
      )}
    </span>
  );
};

export default StarRating;
```

### Step 12：评价表单 — `components/ReviewForm.tsx`

```tsx
import React, { useState } from 'react';
import StarRating from './StarRating';

interface ReviewFormProps {
  productId: number;
  orderId: number;
  productName: string;
  onSubmit: (data: { product_id: number; order_id: number; rating: number; content: string }) => Promise<void>;
  onClose: () => void;
}

const ReviewForm: React.FC<ReviewFormProps> = ({ productId, orderId, productName, onSubmit, onClose }) => {
  const [rating, setRating] = useState(0);
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      alert('请选择评分');
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit({ product_id: productId, order_id: orderId, rating, content });
      alert('评价提交成功！');
      onClose();
    } catch {
      alert('评价提交失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px' }}>
      <h3>评价 {productName}</h3>
      <div style={{ margin: '16px 0' }}>
        <div style={{ marginBottom: '8px', color: '#374151' }}>评分：</div>
        {rating === 0 && <div style={{ fontSize: '12px', color: '#ef4444', marginBottom: '4px' }}>请选择评分</div>}
        <StarRating rating={rating} size="lg" interactive onChange={setRating} />
      </div>
      <textarea
        placeholder="分享你的使用体验..."
        value={content}
        onChange={e => setContent(e.target.value)}
        maxLength={2000}
        rows={4}
        style={{
          width: '100%',
          padding: '8px',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          resize: 'vertical',
          boxSizing: 'border-box',
        }}
      />
      <div style={{ textAlign: 'right', fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
        {content.length}/2000
      </div>
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '16px' }}>
        <button onClick={onClose} disabled={submitting}
          style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #d1d5db', cursor: 'pointer' }}>
          取消
        </button>
        <button onClick={handleSubmit} disabled={submitting || rating === 0}
          style={{
            padding: '8px 16px', borderRadius: '6px', border: 'none',
            backgroundColor: rating > 0 ? '#3b82f6' : '#9ca3af',
            color: '#fff', cursor: rating > 0 ? 'pointer' : 'not-allowed',
          }}>
          {submitting ? '提交中...' : '提交评价'}
        </button>
      </div>
    </div>
  );
};

export default ReviewForm;
```

### Step 13：商品详情页评价区域 — `ProductDetailPage.tsx`

在商品信息下方新增评价 Tab/区域：

```tsx
// 在 ProductDetailPage 组件内添加
import { useState, useEffect } from 'react';
import StarRating from '../../components/StarRating';
import { getProductReviews, getProductReviewStats } from '../../api/review';
import type { Review, ReviewStats } from '../../types';

// 在组件内
const [activeTab, setActiveTab] = useState<'details' | 'reviews'>('details');
const [reviews, setReviews] = useState<Review[]>([]);
const [reviewStats, setReviewStats] = useState<ReviewStats | null>(null);
const [reviewPage, setReviewPage] = useState(1);

// 加载评价数据
useEffect(() => {
  if (product?.id) {
    getProductReviews(product.id, reviewPage).then(r => {
      if (r.code === 0) setReviews(r.data.items);
    });
    getProductReviewStats(product.id).then(r => {
      if (r.code === 0) setReviewStats(r.data);
    });
  }
}, [product?.id, reviewPage]);

// 渲染 Tab 切换
const renderReviews = () => (
  <div>
    {reviewStats && (
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '36px', fontWeight: 'bold' }}>{reviewStats.avg_rating.toFixed(1)}</div>
          <StarRating rating={Math.round(reviewStats.avg_rating)} size="sm" />
          <div style={{ fontSize: '12px', color: '#6b7280' }}>{reviewStats.total_count} 条评价</div>
        </div>
        <div style={{ flex: 1 }}>
          {[5, 4, 3, 2, 1].map(star => (
            <div key={star} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '12px', width: '20px' }}>{star}星</span>
              <div style={{ flex: 1, height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${reviewStats.total_count > 0 ? (reviewStats.distribution[star] || 0) / reviewStats.total_count * 100 : 0}%`,
                  backgroundColor: '#f59e0b',
                  borderRadius: '4px',
                }} />
              </div>
              <span style={{ fontSize: '12px', color: '#6b7280', width: '24px', textAlign: 'right' }}>
                {reviewStats.distribution[star] || 0}
              </span>
            </div>
          ))}
        </div>
      </div>
    )}
    {reviews.length === 0 ? (
      <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>暂无评价</div>
    ) : (
      reviews.map(review => (
        <div key={review.id} style={{ padding: '12px 0', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <StarRating rating={review.rating} size="sm" />
            <span style={{ fontSize: '14px', color: '#374151' }}>{review.nickname || '匿名用户'}</span>
            <span style={{ fontSize: '12px', color: '#9ca3af' }}>{review.created_at?.slice(0, 10)}</span>
          </div>
          <div style={{ fontSize: '14px', color: '#4b5563' }}>{review.content}</div>
        </div>
      ))
    )}
  </div>
);
```

### Step 14：订单详情页修改 — `OrderDetailPage.tsx`

#### 14a. 支付方式选择弹窗

在 `handlePay` 之前新增支付方式选择：

```tsx
// 替换原有的 handlePay
const [showPaymentModal, setShowPaymentModal] = useState(false);
const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('wechat');
const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'failed'>('idle');

const PAYMENT_METHODS: { key: PaymentMethod; label: string; icon: string }[] = [
  { key: 'wechat', label: '微信支付', icon: '💚' },
  { key: 'alipay', label: '支付宝', icon: '💙' },
  { key: 'card', label: '银行卡', icon: '💳' },
  { key: 'balance', label: '余额支付', icon: '💰' },
];

const handlePaySubmit = async () => {
  setShowPaymentModal(false);
  setPaymentStatus('processing');
  try {
    const r = await payOrder(Number(id), paymentMethod);
    if (r.code === 0) {
      // 轮询支付状态
      const poll = setInterval(async () => {
        const status = await getPaymentStatus(Number(id));
        if (status.data?.status === 'success') {
          setPaymentStatus('success');
          clearInterval(poll);
          fetchOrder(); // 刷新订单
        } else if (status.data?.status === 'failed') {
          setPaymentStatus('failed');
          clearInterval(poll);
        }
      }, 1000);
      setTimeout(() => clearInterval(poll), 10000); // 10秒超时
    } else {
      setPaymentStatus('failed');
    }
  } catch {
    setPaymentStatus('failed');
  }
};
```

#### 14b. 评价入口

在已支付的订单商品列表中添加"去评价"按钮：

```tsx
// 在订单状态为 paid 时，每个商品显示"去评价"
{order.status === 'paid' && (
  <button onClick={() => {
    setReviewProduct(item);
    setShowReview(true);
  }}
  style={{ padding: '4px 12px', fontSize: '12px', borderRadius: '4px', border: '1px solid #3b82f6', color: '#3b82f6', cursor: 'pointer' }}>
    去评价
  </button>
)}
```

### Step 15：修改 `api/order.ts` — payOrder 支持 payment_method

```typescript
// 原有
export async function payOrder(id: number) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/pay`);
}

// 改为
export async function payOrder(id: number, paymentMethod?: string) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/pay`, {
    payment_method: paymentMethod || 'mock',
  });
}

// 新增：查询支付状态
export async function getPaymentStatus(id: number) {
  return client.get<any, ApiResponse<PaymentRecord>>(`/c-endpoint/orders/${id}/payment`);
}
```

### Step 16-17：ChatPopup 增强

#### 16a. 下单卡片

在 AI 回复中检测订单信息，渲染为可点击订单卡片：

```tsx
// 在 ChatPopup.tsx 中，消息渲染部分
const renderMessage = (msg: Message) => {
  if (msg.role === 'user') return <div className="user-msg">{msg.content}</div>;

  // 检测是否包含订单信息（从 data 字段获取）
  const orderData = msg.data?.order;
  const paymentData = msg.data?.payment;
  const reviewData = msg.data?.review;

  return (
    <div className="assistant-msg">
      <Markdown>{msg.content}</Markdown>
      {orderData && (
        <div className="order-card" onClick={() => navigate(`/orders/${orderData.id}`)}>
          <div>📦 订单 #{orderData.id}</div>
          <div>金额: ¥{orderData.total_amount}</div>
          <div>状态: {orderData.status === 'pending' ? '待支付' : '已创建'}</div>
        </div>
      )}
      {paymentData && (
        <div className="payment-status">
          {paymentData.status === 'success' ? '✅ 支付成功' : '⏳ 支付处理中...'}
        </div>
      )}
      {reviewData && (
        <div className="review-summary">
          <div>⭐ 平均评分: {reviewData.stats?.avg_rating}/5</div>
          <div>📊 共 {reviewData.stats?.total_count} 条评价</div>
        </div>
      )}
    </div>
  );
};
```

#### 16b. 支付快捷按钮

```tsx
// 在聊天输入框上方，当 AI 询问支付方式时显示
{showPaymentButtons && (
  <div className="payment-quick-buttons">
    {['wechat', 'alipay', 'card', 'balance'].map(method => (
      <button key={method} onClick={() => handleQuickPay(method)}>
        {method === 'wechat' ? '💚 微信支付' :
         method === 'alipay' ? '💙 支付宝' :
         method === 'card' ? '💳 银行卡' : '💰 余额'}
      </button>
    ))}
  </div>
)}
```

#### 16c. ChatPopup.css 新增样式

```css
/* 订单卡片 */
.order-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  cursor: pointer;
  transition: box-shadow 0.2s;
  background: #f9fafb;
}
.order-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 支付快捷按钮 */
.payment-quick-buttons {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
}
.payment-quick-buttons button {
  padding: 6px 14px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}
.payment-quick-buttons button:hover {
  background: #f3f4f6;
}

/* 评价总结 */
.review-summary {
  border: 1px solid #fef3c7;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  background: #fffbeb;
}

/* 支付状态 */
.payment-status {
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 6px;
  font-weight: 500;
}
```

---

## 五、接口依赖

| 你的工作 | 依赖 | 对方 |
|----------|------|------|
| `create_order` tool + shop_client | `POST /internal/orders/create` | 小C |
| `pay_order` tool + shop_client | `POST /c-endpoint/orders/{id}/pay` | 小C |
| `get_product_reviews` tool | `GET /internal/reviews/product/{id}` | 小B |
| 前端评价 API | `GET /c-endpoint/reviews/product/{id}` | 小B |

**建议**：先与小B、小C确认接口契约（请求/响应格式），然后可以先用 mock 数据开发，后端就绪后联调。

---

## 六、自测清单

| # | 测试项 | 预期 |
|:-:|--------|------|
| 1 | FAQ 检索命中"退货需要什么条件" | 直接返回 FAQ 答案，不调 LLM |
| 2 | FAQ 未命中问题 | 降级到 LLM 工具调用 |
| 3 | AI 调用 create_order 成功 | 数据库订单创建 |
| 4 | AI 调用 pay_order 成功 | 支付记录状态更新 |
| 5 | AI 调用 get_product_reviews | 返回评价数据 + 统计 |
| 6 | 对话创建后在数据库持久化 | 查询 customer_service.messages 有记录 |
| 7 | 前端 StarRating 展示/交互模式正常 | 展示模式只读，交互模式可点击 |
| 8 | 前端评价表单提交 | 评价成功写入 |
| 9 | 前端支付方式选择弹窗 | 选择后调用 payOrder 传递 payment_method |
| 10 | 前端 ChatPopup 订单卡片渲染 | AI 回复中订单信息可点击 |

---

## 七、FAQ 种子数据

FAQ 种子数据脚本位于 `ai-service/scripts/seed_faq.py`，包含 26 条常见问答。
你需要先完成 `faq_service.py`（含 embedding 生成），然后运行该脚本：

```bash
cd ai-service
pip install -r requirements.txt  # 确保已加 psycopg2-binary
python scripts/seed_faq.py --dry-run  # 预览
python scripts/seed_faq.py            # 正式导入
```
