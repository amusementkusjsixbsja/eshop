# 🅱️ 小B — 第二轮开发指南：商品评价系统

> **分支：** `feat/xiaob-reviews`
> **服务：** `service-user-product`（端口 8001）+ 数据库
> **依赖：** 无（独立开发）
> **预计工作量：** 5 个文件

---

## 一、任务总览

| 序号 | 文件 | 操作 | 说明 |
|:----:|------|:----:|------|
| 1 | `docker/init.sql` | 修改 | 新增 `shop.reviews` 表 + `shop.products` 扩展字段 |
| 2 | `service-user-product/services/review_service.py` | ✅ 新建 | 评价业务逻辑层 |
| 3 | `service-user-product/routers/review_router.py` | ✅ 新建 | 评价 API 端点 |
| 4 | `service-user-product/routers/internal_router.py` | 修改 | 新增评价内部接口（供 AI 服务调用） |
| 5 | `service-user-product/services/product_service.py` | 修改 | `get_product_by_id()` 附加评分信息 |
| 6 | `service-user-product/main.py` | 修改 | 注册 `review_router` |

---

## 二、详细实现步骤

### Step 1：数据库变更 — `docker/init.sql`

在 `shop.after_sale_requests` 表定义之后（第 148 行）、`customer_service` schema 之前插入：

```sql
-- ============================================
-- 商品评价表（v2.0）
-- ============================================
CREATE TABLE IF NOT EXISTS shop.reviews (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES shop.products(id),
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    rating      SMALLINT NOT NULL CHECK(rating >= 1 AND rating <= 5),
    content     TEXT DEFAULT '',
    status      VARCHAR(20) DEFAULT 'visible',     -- visible / hidden
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, order_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_product ON shop.reviews(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON shop.reviews(user_id);

-- 商品表新增评分缓存字段
ALTER TABLE shop.products ADD COLUMN IF NOT EXISTS avg_rating DECIMAL(3,2) DEFAULT 0;
ALTER TABLE shop.products ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
```

**验证：** 重建数据库后运行 `\d shop.reviews` 和 `\d shop.products` 确认表结构正确。

---

### Step 2：创建 `services/review_service.py`

**文件路径：** `service-user-product/services/review_service.py`

要点：
- 复用 `shop_shared.infrastructure.database` 的 `get_connection()` / `get_cursor()` 模式
- 所有数据库操作使用 `psycopg2.extras.RealDictCursor`
- 返回字典格式数据（不要返回 ORM 对象）

```python
"""商品评价业务逻辑层。"""

from datetime import datetime
from psycopg2 import extras
from shop_shared.infrastructure.database import get_connection, release_connection
from shop_shared.common.exceptions import NotFoundError, BusinessError


def create_review(user_id: int, product_id: int, order_id: int, rating: int, content: str) -> dict:
    """创建评价。

    校验：
    1. 订单归属于当前用户
    2. 订单状态为 paid（已支付）
    3. 未对该商品评价过（UNIQUE 约束兜底）

    成功后更新 products 表的 avg_rating 和 review_count。
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 1. 校验订单归属 & 支付状态
        cur.execute("""
            SELECT id, user_id, status FROM shop.orders WHERE id = %s
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise BusinessError("无权评价该订单")
        if order["status"] != "paid":
            raise BusinessError("仅已支付的订单可以评价")

        # 2. 校验未重复评价（应用层 + 数据库 UNIQUE 双重保障）
        cur.execute("""
            SELECT id FROM shop.reviews
            WHERE user_id = %s AND order_id = %s AND product_id = %s
        """, (user_id, order_id, product_id))
        if cur.fetchone():
            raise BusinessError("已评价过该商品")

        # 3. 校验商品存在
        cur.execute("SELECT id FROM shop.products WHERE id = %s", (product_id,))
        if not cur.fetchone():
            raise NotFoundError("商品不存在")

        # 4. 插入评价
        cur.execute("""
            INSERT INTO shop.reviews (product_id, user_id, order_id, rating, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, product_id, user_id, order_id, rating, content, status, created_at
        """, (product_id, user_id, order_id, rating, content))
        review = dict(cur.fetchone())

        # 5. 更新商品评分缓存
        _update_product_rating(cur, product_id)

        conn.commit()
        return review
    except (NotFoundError, BusinessError):
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def get_product_reviews(product_id: int, page: int = 1, size: int = 10) -> tuple:
    """获取商品评价列表（分页，按时间倒序，仅 visible 状态）。

    Returns:
        (items: list[dict], total: int)
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 查询总数
        cur.execute("""
            SELECT COUNT(*) FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
        """, (product_id,))
        total = cur.fetchone()["count"]

        # 查询列表（JOIN users 获取 nickname）
        offset = (page - 1) * size
        cur.execute("""
            SELECT r.id, r.product_id, r.user_id, u.nickname,
                   r.rating, r.content, r.status, r.created_at
            FROM shop.reviews r
            LEFT JOIN shop.users u ON r.user_id = u.id
            WHERE r.product_id = %s AND r.status = 'visible'
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """, (product_id, size, offset))
        items = [dict(row) for row in cur.fetchall()]

        return items, total
    finally:
        release_connection(conn)


def get_review_stats(product_id: int) -> dict:
    """获取商品评价统计。

    Returns:
        {"avg_rating": float, "total_count": int, "distribution": {1: int, 2: int, 3: int, 4: int, 5: int}}
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 平均分 + 总数
        cur.execute("""
            SELECT COALESCE(AVG(rating), 0)::numeric(3,2) as avg_rating,
                   COUNT(*) as total_count
            FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
        """, (product_id,))
        stats = dict(cur.fetchone())

        # 各星级分布
        cur.execute("""
            SELECT rating, COUNT(*) as count
            FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
            GROUP BY rating
            ORDER BY rating
        """, (product_id,))
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for row in cur.fetchall():
            distribution[row["rating"]] = row["count"]

        stats["distribution"] = distribution
        return stats
    finally:
        release_connection(conn)


def get_user_reviews(user_id: int) -> list:
    """获取当前用户的评价列表。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT r.id, r.product_id, p.name as product_name, r.order_id,
                   r.rating, r.content, r.created_at
            FROM shop.reviews r
            LEFT JOIN shop.products p ON r.product_id = p.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """, (user_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)


def _update_product_rating(cur, product_id: int):
    """更新商品的评分缓存字段（内部辅助函数）。"""
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
    """, (product_id, product_id, product_id))
```

---

### Step 3：创建 `routers/review_router.py`

```python
"""商品评价 — 前端 API 端点。"""

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field

from shop_shared.common import success_response
from shop_shared.common.exceptions import NotFoundError, BusinessError
from shop_shared.middleware import get_current_user

from services.review_service import (
    create_review,
    get_product_reviews,
    get_review_stats,
    get_user_reviews,
)

router = APIRouter(prefix="/c-endpoint", tags=["商品评价"])


class CreateReviewRequest(BaseModel):
    product_id: int = Field(..., description="商品 ID")
    order_id: int = Field(..., description="订单 ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    content: str = Field(default="", max_length=2000, description="评价内容")


@router.post("/reviews")
def create_review_handler(req: CreateReviewRequest, user=Depends(get_current_user)):
    """创建商品评价（需登录、仅已支付订单）。"""
    review = create_review(
        user_id=user["id"],
        product_id=req.product_id,
        order_id=req.order_id,
        rating=req.rating,
        content=req.content,
    )
    return success_response(review)


@router.get("/reviews/product/{product_id}")
def list_product_reviews(
    product_id: int = Path(..., description="商品 ID"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
):
    """获取商品评价列表（公开，仅 visible 状态）。"""
    items, total = get_product_reviews(product_id, page, size)
    return success_response({"items": items, "total": total, "page": page, "size": size})


@router.get("/reviews/product/{product_id}/stats")
def product_review_stats(product_id: int = Path(..., description="商品 ID")):
    """获取商品评价统计（公开）。"""
    stats = get_review_stats(product_id)
    return success_response(stats)


@router.get("/reviews/user/me")
def user_reviews(user=Depends(get_current_user)):
    """获取当前用户的评价列表（需登录）。"""
    reviews = get_user_reviews(user["id"])
    return success_response(reviews)
```

---

### Step 4：修改 `routers/internal_router.py`

在现有内部端点末尾追加两个评价相关端点：

```python
# ─── 评价内部接口（供 ai-service 调用）───

@router.get("/reviews/product/{product_id}")
def internal_product_reviews(product_id: int):
    """获取商品最新评价（用于 AI 总结，取最近 20 条）。"""
    from services.review_service import get_product_reviews, get_review_stats
    items, total = get_product_reviews(product_id, page=1, size=20)
    stats = get_review_stats(product_id)
    return success_response({"reviews": items, "stats": stats})


@router.get("/reviews/product/{product_id}/stats")
def internal_product_review_stats(product_id: int):
    """获取商品评价统计（avg_rating, distribution）。"""
    from services.review_service import get_review_stats
    return success_response(get_review_stats(product_id))
```

---

### Step 5：修改 `services/product_service.py`

在 `get_product_by_id()` 返回的字典中附加 `avg_rating` 和 `review_count`：

```python
def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    # ... 原有缓存/查询逻辑不变 ...
    product = dict(row)

    # 附加评价统计
    product["avg_rating"] = float(row.get("avg_rating", 0)) if row.get("avg_rating") else 0
    product["review_count"] = row.get("review_count", 0) or 0

    return product
```

注意：`avg_rating` 在 `ALTER TABLE` 后已经存在于 `products` 表，`SELECT *` 可以获取到。只需转为 float 即可。

---

### Step 6：修改 `main.py`

```python
# 在一堆 import 中添加
from routers.review_router import router as review_router

# 在 app.include_router(...) 组中添加
app.include_router(review_router, prefix="/c-endpoint")
```

---

## 三、接口契约

### 公开 API

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/shop/c-endpoint/reviews` | 创建评价 | JWT |
| GET | `/api/shop/c-endpoint/reviews/product/{id}` | 评价列表（分页） | 公开 |
| GET | `/api/shop/c-endpoint/reviews/product/{id}/stats` | 评价统计 | 公开 |
| GET | `/api/shop/c-endpoint/reviews/user/me` | 我的评价 | JWT |

### 内部接口（供 ai-service）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/internal/reviews/product/{id}` | 评价数据（最新20条+统计） |
| GET | `/internal/reviews/product/{id}/stats` | 评价统计 |

### 通用响应格式

```json
{"code": 0, "data": {...}, "message": "success"}
```

---

## 四、自测清单

| # | 测试项 | 预期 |
|:-:|--------|------|
| 1 | 正常用户评价已支付订单商品 | 返回评价记录，code=0 |
| 2 | 重复评价同一商品 | 返回错误，code≠0 |
| 3 | 未支付订单评价 | 返回业务错误 |
| 4 | 无 token 创建评价 | 返回鉴权错误 |
| 5 | 商品评价列表有分页 | 支持 page/size 参数 |
| 6 | 评价统计各星级正确 | distribution 5 个星级齐全 |
| 7 | 商品详情页显示评分 | `avg_rating` 和 `review_count` 有值 |

---

## 五、依赖关系

- ✅ **无外部依赖**：本模块可独立开发、独立测试
- ➡️ **被依赖**：小A 的 AI 评价总结需要你的内部接口
- ➡️ **被依赖**：小D 的管理后台评价管理需要你的数据

---

## 六、测试数据

评价测试数据脚本位于 `scripts/seed_review_data.py`，包含 9 个商品的 100+ 条模拟评价。运行方式：

```bash
# 先完成数据库迁移并启动服务
cd docker && docker compose down -v && docker compose up -d
# 安装依赖
pip install psycopg2-binary
# 查看预览
python scripts/seed_review_data.py --dry-run
# 正式导入
python scripts/seed_review_data.py
```
