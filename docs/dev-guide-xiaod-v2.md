# 🅳 小D — 第二轮开发指南：管理后台 + 基础设施 + 集成测试

> **分支：** `feat/xiaod-admin-infra`
> **服务：** `service-admin`（端口 8003）+ 全局配置 + 测试
> **依赖：** 小B（评价数据库 schema 完成后可测试管理功能）
> **预计工作量：** 8 个文件

---

## 一、任务总览

| 序号 | 文件 | 操作 | 说明 |
|:----:|------|:----:|------|
| 1 | `service-admin/routers/review_router.py` | ✅ 新建 | 评价管理后台路由 |
| 2 | `service-admin/services/review_service.py` | ✅ 新建 | 评价管理后台业务逻辑 |
| 3 | `service-admin/routers/faq_router.py` | ✅ 新建 | FAQ 管理后台路由 |
| 4 | `service-admin/services/faq_admin_service.py` | ✅ 新建 | FAQ 管理后台业务逻辑 |
| 5 | `service-admin/main.py` | 修改 | 注册新路由 |
| 6 | `docker/nginx/nginx.conf` | 修改 | 新增 reviews + faq 路由 |
| 7 | `docker/docker-compose.yml` | 修改 | ai-service 新增 DATABASE_URL |
| 8 | `tests/integration_test.py` | 修改 | 新增 15+ 测试用例 |

---

## 二、详细实现步骤

### Step 1：管理后台 — 评价管理

#### 1a. 创建 `services/review_service.py`

**文件路径：** `service-admin/services/review_service.py`

管理员评价管理直接查数据库（不走内部接口），复用 `shop_shared.infrastructure.database`：

```python
"""管理后台 — 评价管理业务逻辑。"""

from psycopg2 import extras
from shop_shared.infrastructure.database import get_connection, release_connection
from shop_shared.common.exceptions import NotFoundError


def get_all_reviews(page: int = 1, size: int = 20, product_id: int = None, rating: int = None) -> tuple:
    """获取全部评价列表（管理后台，含隐藏评价）。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        conditions = []
        params = []
        if product_id:
            conditions.append("r.product_id = %s")
            params.append(product_id)
        if rating:
            conditions.append("r.rating = %s")
            params.append(rating)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        # 总数
        cur.execute(f"SELECT COUNT(*) FROM shop.reviews r {where}", params)
        total = cur.fetchone()["count"]

        # 列表
        offset = (page - 1) * size
        cur.execute(f"""
            SELECT r.*, p.name as product_name, u.nickname as user_nickname
            FROM shop.reviews r
            LEFT JOIN shop.products p ON r.product_id = p.id
            LEFT JOIN shop.users u ON r.user_id = u.id
            {where}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [size, offset])
        items = [dict(row) for row in cur.fetchall()]

        return items, total
    finally:
        release_connection(conn)


def set_review_status(review_id: int, status: str) -> dict:
    """隐藏/显示评价（visible ↔ hidden）。"""
    if status not in ("visible", "hidden"):
        raise ValueError("状态值必须为 visible 或 hidden")

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            UPDATE shop.reviews
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, product_id, user_id, rating, content, status, created_at
        """, (status, review_id))
        review = cur.fetchone()
        if not review:
            raise NotFoundError("评价不存在")

        # 同步更新 products 表的评分缓存
        cur.execute("""
            UPDATE shop.products
            SET avg_rating = (
                SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0)
                FROM shop.reviews WHERE product_id = %s AND status = 'visible'
            ),
            review_count = (
                SELECT COUNT(*) FROM shop.reviews WHERE product_id = %s AND status = 'visible'
            )
            WHERE id = %s
        """, (review["product_id"], review["product_id"], review["product_id"]))

        conn.commit()
        return dict(review)
    except NotFoundError:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def get_product_reviews_for_admin(product_id: int) -> list:
    """获取某商品的全部评价（管理后台，含隐藏评价）。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT r.*, u.nickname as user_nickname
            FROM shop.reviews r
            LEFT JOIN shop.users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.created_at DESC
        """, (product_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)
```

#### 1b. 创建 `routers/review_router.py`

```python
"""管理后台 — 评价管理路由。"""

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field

from shop_shared.common import success_response
from shop_shared.middleware import get_current_admin
from services.review_service import (
    get_all_reviews,
    set_review_status,
    get_product_reviews_for_admin,
)

router = APIRouter(prefix="/b-endpoint", tags=["管理后台-评价"])


class SetReviewStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(visible|hidden)$")


@router.get("/reviews")
def list_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    product_id: int = Query(None, description="按商品筛选"),
    rating: int = Query(None, ge=1, le=5, description="按星级筛选"),
    admin=Depends(get_current_admin),
):
    """评价列表（分页，支持筛选）。"""
    items, total = get_all_reviews(page, size, product_id, rating)
    return success_response({"items": items, "total": total, "page": page, "size": size})


@router.patch("/reviews/{review_id}/status")
def update_review_status(
    review_id: int,
    req: SetReviewStatusRequest,
    admin=Depends(get_current_admin),
):
    """隐藏/显示评价。"""
    review = set_review_status(review_id, req.status)
    return success_response(review)


@router.get("/reviews/product/{product_id}")
def list_product_reviews_admin(
    product_id: int,
    admin=Depends(get_current_admin),
):
    """某商品的全部评价管理。"""
    reviews = get_product_reviews_for_admin(product_id)
    return success_response({"items": reviews})
```

---

### Step 2：管理后台 — FAQ 管理

#### 2a. 创建 `services/faq_admin_service.py`

```python
"""管理后台 — FAQ 知识库管理业务逻辑。"""

import json
from psycopg2 import extras
from shop_shared.infrastructure.database import get_connection, release_connection
from shop_shared.common.exceptions import NotFoundError


def get_all_faqs(category: str = None) -> list:
    """获取 FAQ 列表。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        if category:
            cur.execute("""
                SELECT id, question, answer, metadata, created_at
                FROM customer_service.faq_embeddings
                WHERE metadata->>'category' = %s
                ORDER BY id
            """, (category,))
        else:
            cur.execute("""
                SELECT id, question, answer, metadata, created_at
                FROM customer_service.faq_embeddings
                ORDER BY id
            """)
        items = []
        for row in cur.fetchall():
            item = dict(row)
            if isinstance(item.get("metadata"), str):
                item["metadata"] = json.loads(item["metadata"])
            items.append(item)
        return items
    finally:
        release_connection(conn)


def add_faq(question: str, answer: str, category: str = "general") -> dict:
    """添加 FAQ 条目（embedding 由 ai-service 异步生成）。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        metadata = json.dumps({"category": category})
        # 先插入数据，embedding 用零向量占位，由 ai-service 后续补全
        import struct
        zero_embedding = [0.0] * 1024
        cur.execute("""
            INSERT INTO customer_service.faq_embeddings (question, answer, embedding, metadata)
            VALUES (%s, %s, %s::vector, %s)
            RETURNING id, question, answer, metadata, created_at
        """, (question, answer, zero_embedding, metadata))
        faq = dict(cur.fetchone())
        conn.commit()
        if isinstance(faq.get("metadata"), str):
            faq["metadata"] = json.loads(faq["metadata"])
        # 去除 embedding（不需要返回给前端）
        faq.pop("embedding", None)
        return faq
    finally:
        release_connection(conn)


def update_faq(faq_id: int, question: str = None, answer: str = None, category: str = None) -> dict:
    """修改 FAQ 条目。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 构建动态 UPDATE
        sets = []
        params = []
        if question is not None:
            sets.append("question = %s")
            params.append(question)
        if answer is not None:
            sets.append("answer = %s")
            params.append(answer)
        if category is not None:
            metadata = json.dumps({"category": category})
            sets.append("metadata = %s")
            params.append(metadata)

        if not sets:
            raise ValueError("没有需要更新的字段")

        params.append(faq_id)
        cur.execute(f"""
            UPDATE customer_service.faq_embeddings
            SET {', '.join(sets)}
            WHERE id = %s
            RETURNING id, question, answer, metadata, created_at
        """, params)
        faq = cur.fetchone()
        if not faq:
            raise NotFoundError("FAQ 不存在")
        conn.commit()
        return dict(faq)
    except NotFoundError:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def delete_faq(faq_id: int):
    """删除 FAQ 条目。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            DELETE FROM customer_service.faq_embeddings WHERE id = %s
            RETURNING id
        """, (faq_id,))
        if not cur.fetchone():
            raise NotFoundError("FAQ 不存在")
        conn.commit()
    except NotFoundError:
        conn.rollback()
        raise
    finally:
        release_connection(conn)
```

#### 2b. 创建 `routers/faq_router.py`

```python
"""管理后台 — FAQ 知识库管理路由。"""

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field

from shop_shared.common import success_response
from shop_shared.middleware import get_current_admin
from services.faq_admin_service import (
    get_all_faqs,
    add_faq,
    update_faq,
    delete_faq,
)

router = APIRouter(prefix="/b-endpoint", tags=["管理后台-FAQ"])


class AddFaqRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="general", max_length=50)


class UpdateFaqRequest(BaseModel):
    question: str = Field(None, min_length=1, max_length=500)
    answer: str = Field(None, min_length=1, max_length=2000)
    category: str = Field(None, max_length=50)


@router.get("/faq")
def list_faqs(
    category: str = Query(None, description="按分类筛选"),
    admin=Depends(get_current_admin),
):
    """FAQ 列表。"""
    faqs = get_all_faqs(category)
    return success_response({"items": faqs})


@router.post("/faq")
def create_faq(
    req: AddFaqRequest,
    admin=Depends(get_current_admin),
):
    """添加 FAQ。"""
    faq = add_faq(req.question, req.answer, req.category)
    return success_response(faq)


@router.put("/faq/{faq_id}")
def edit_faq(
    faq_id: int,
    req: UpdateFaqRequest,
    admin=Depends(get_current_admin),
):
    """修改 FAQ。"""
    faq = update_faq(faq_id, req.question, req.answer, req.category)
    return success_response(faq)


@router.delete("/faq/{faq_id}")
def remove_faq(
    faq_id: int,
    admin=Depends(get_current_admin),
):
    """删除 FAQ。"""
    delete_faq(faq_id)
    return success_response({"deleted": True})
```

---

### Step 3：注册路由 — `service-admin/main.py`

```python
# 在顶部 import 区添加
from routers.review_router import router as review_router
from routers.faq_router import router as faq_router

# 在 app.include_router 组中添加
app.include_router(review_router)
app.include_router(faq_router)
```

---

### Step 4：Nginx 路由 — `docker/nginx/nginx.conf`

#### 4a. user-product 区域新增 reviews 路由

找到 user-product 的 location 块，在最后新增：

```nginx
# 商品评价（v2.0）
location ~ ^/api/shop/c-endpoint/reviews/(.*)$ {
    set $upstream_path /c-endpoint/reviews/$1$is_args$args;
    proxy_pass http://user-product:8001$upstream_path;
}
```

#### 4b. admin 区域新增 reviews 和 faq 管理路由

找到 admin 的 location 块，确认已经覆盖 `/api/shop/b-endpoint/`：

```nginx
# 管理后台
location /api/shop/b-endpoint/ {
    proxy_pass http://admin:8003/b-endpoint/;
}
```

如果已存在上述配置则无需修改（b-endpoint 下新增的路由会自动匹配）。

---

### Step 5：Docker Compose — `docker/docker-compose.yml`

在 `ai-service` 配置段的 `environment` 中新增：

```yaml
ai-service:
  build:
    context: ../ai-service
  environment:
    - JWT_SECRET=${JWT_SECRET:-dev-secret-change-in-production}
    - INTERNAL_API_TOKEN=${INTERNAL_API_TOKEN:-dev-internal-token}
    - USER_INTERNAL_URL=http://user-product:8001/internal
    - ORDER_INTERNAL_URL=http://order-trade:8002/internal
    - MOCK_MODE=false
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
    # ✅ 新增：数据库连接（供 FAQ 检索 + 对话持久化）
    - DATABASE_URL=${DATABASE_URL:-postgresql://user:1234@postgres:5432/agent}
```

---

### Step 6：集成测试 — `tests/integration_test.py`

#### 6a. 新增测试函数：评价测试

在 `test_ai` 函数之后新增 `test_reviews_v2` 函数，并注册到 main() 中：

```python
def test_reviews_v2(api: HttpClient):
    section("12. 评价系统（v2.0）")
    if not api.token:
        log(False, "评价测试", "跳过（无 token）"); return

    # 12.1 先下单并支付（用于后续评价）
    api.post("/api/shop/c-endpoint/cart",
             {"product_id": 4, "quantity": 1}, token=api.token)
    r = api.post("/api/shop/c-endpoint/orders",
                 {"address": "评价测试地址"}, token=api.token)
    oid = r.get("data", {}).get("id") if r.get("data") else None
    if not oid:
        log(False, "创建订单", "无法创建订单供评价测试"); return

    # 支付该订单
    r = api.post(f"/api/shop/c-endpoint/orders/{oid}/pay",
                 {"payment_method": "mock"}, token=api.token)
    log(r.get("code") == 0, f"支付订单 #{oid}")
    time.sleep(3)

    # 12.2 创建评价
    r = api.post("/api/shop/c-endpoint/reviews",
                 {"product_id": 4, "order_id": oid, "rating": 5, "content": "很好用！"},
                 token=api.token)
    rid = r.get("data", {}).get("id") if r.get("data") else None
    log(r.get("code") == 0 and rid is not None, f"创建评价 #{rid}")

    # 12.3 重复评价拒绝
    if rid:
        r = api.post("/api/shop/c-endpoint/reviews",
                     {"product_id": 4, "order_id": oid, "rating": 3, "content": "重复评价"},
                     token=api.token)
        log(r.get("code") != 0, "重复评价拒绝")

    # 12.4 评价列表
    r = api.get("/api/shop/c-endpoint/reviews/product/4")
    log(r.get("code") == 0, "商品评价列表")
    items = r.get("data", {}).get("items", [])
    if items:
        log(any(item.get("id") == rid for item in items), "列表包含刚创建的评价")

    # 12.5 评价统计
    r = api.get("/api/shop/c-endpoint/reviews/product/4/stats")
    log(r.get("code") == 0, "评价统计")
    dist = r.get("data", {}).get("distribution", {})
    if dist:
        log(dist.get("5", 0) > 0, f"评分分布正确")

    # 12.6 无 token 拒绝创建评价
    r = api.post("/api/shop/c-endpoint/reviews",
                 {"product_id": 4, "order_id": oid, "rating": 4, "content": "无权限"},
                 token="invalid")
    log(r.get("code") != 0, "无token拒绝创建评价")
```

#### 6b. 新增测试函数：支付增强测试

```python
def test_payment_v2(api: HttpClient):
    section("13. 模拟支付增强（v2.0）")
    if not api.token:
        log(False, "支付增强测试", "跳过（无 token）"); return

    # 13.1 创建订单用于支付测试
    api.post("/api/shop/c-endpoint/cart",
             {"product_id": 1, "quantity": 1}, token=api.token)
    r = api.post("/api/shop/c-endpoint/orders",
                 {"address": "支付测试地址"}, token=api.token)
    oid = r.get("data", {}).get("id") if r.get("data") else None
    if not oid:
        log(False, "创建订单", "无法创建订单供支付测试"); return

    # 13.2 使用支付宝支付
    r = api.post(f"/api/shop/c-endpoint/orders/{oid}/pay",
                 {"payment_method": "alipay"}, token=api.token)
    pay_id = r.get("data", {}).get("id") if r.get("data") else None
    log(r.get("code") == 0 and r.get("data",{}).get("status") == "processing",
        f"发起支付（支付宝）")

    # 13.3 查询支付状态
    if oid:
        time.sleep(2)
        r = api.get(f"/api/shop/c-endpoint/orders/{oid}/payment", token=api.token)
        log(r.get("code") == 0, "支付状态查询")
```

#### 6c. 注册到 main()

在 `test_ai` 调用之后添加：

```python
    test_reviews_v2(api)
    test_payment_v2(api)
```

#### 6d. 预期测试统计

| 测试模块 | 项数 |
|----------|:----:|
| 评价创建 | 4（创建/重复拒绝/列表/统计） |
| 评价权限 | 2（无token拒绝/已购用户可评） |
| 支付增强 | 3（发起支付/状态查询/各支付方式） |
| 合计新增 | ≥ 15 项 |

预计总测试通过率：`78/78 → 100%`（63 项原有 + 15 项新增）

---

## 三、接口契约

### 管理后台评价 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shop/b-endpoint/reviews` | 评价列表（分页） |
| PATCH | `/api/shop/b-endpoint/reviews/{id}/status` | 隐藏/显示评价 |
| GET | `/api/shop/b-endpoint/reviews/product/{id}` | 某商品评价管理 |

### 管理后台 FAQ API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shop/b-endpoint/faq` | FAQ 列表 |
| POST | `/api/shop/b-endpoint/faq` | 添加 FAQ |
| PUT | `/api/shop/b-endpoint/faq/{id}` | 修改 FAQ |
| DELETE | `/api/shop/b-endpoint/faq/{id}` | 删除 FAQ |

---

## 四、自测清单

| # | 测试项 | 预期 |
|:-:|--------|------|
| 1 | 管理员查看评价列表 | 返回所有评价（含隐藏） |
| 2 | 管理员隐藏评价 | status 变为 hidden，商品页不可见 |
| 3 | 管理员显示评价 | status 变为 visible，商品页可见 |
| 4 | 管理员按商品筛选评价 | 只返回该商品评价 |
| 5 | 管理员查看 FAQ 列表 | 返回所有 FAQ |
| 6 | 管理员添加 FAQ | FAQ 成功写入数据库 |
| 7 | 管理员修改 FAQ | FAQ 内容更新 |
| 8 | 管理员删除 FAQ | FAQ 从数据库移除 |
| 9 | Nginx reviews 路由 | curl 返回 200 |
| 10 | docker-compose ai-service 有 DATABASE_URL | 容器启动时正确注入 |
| 11 | 集成测试全部通过 | 78/78 |

---

## 五、依赖关系

- ⚠️ 评价管理功能依赖小B 完成数据库 schema 变更（`shop.reviews` 表存在）
- ✅ Nginx/Docker Compose 变更完全独立，可先行
- ✅ 集成测试需在所有模块完成后进行（Phase 4）
