"""评价业务逻辑层。

★ 小B：评价相关业务逻辑。

参考：
  - shop_shared.infrastructure.database.get_cursor() — 数据库查询
  - shop_shared.infrastructure.redis_client.get_cache() / set_cache() — 缓存
"""

from typing import Any, Dict, List, Optional

from shop_shared.infrastructure.database import get_cursor
from shop_shared.infrastructure.redis_client import get_cache, set_cache
from shop_shared.common.exceptions import BusinessError

from services.product_service import CACHE_KEY_PRODUCT


def create_review(
    user_id: int,
    product_id: int,
    order_id: int,
    rating: int,
    content: str
) -> Dict:
    """创建评价。"""
    if rating < 1 or rating > 5:
        raise BusinessError("评分必须在 1-5 之间")

    with get_cursor() as cur:
        cur.execute("""
            SELECT o.id, o.status, o.user_id, oi.product_id
            FROM shop.orders o
            JOIN shop.order_items oi ON o.id = oi.order_id
            WHERE o.id = %s
              AND o.user_id = %s
              AND oi.product_id = %s
              AND o.status = 'paid'
            LIMIT 1
        """, (order_id, user_id, product_id))
        order = cur.fetchone()

        if not order:
            raise BusinessError("订单不存在、不属于您、商品不在订单中或订单未支付")

    with get_cursor() as cur:
        cur.execute("""
            SELECT id FROM shop.reviews
            WHERE user_id = %s AND order_id = %s AND product_id = %s
        """, (user_id, order_id, product_id))
        existing = cur.fetchone()

        if existing:
            raise BusinessError("您已评价过此商品")

    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO shop.reviews (product_id, user_id, order_id, rating, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (product_id, user_id, order_id, rating, content))
        review = cur.fetchone()

    update_product_rating_cache(product_id)

    return {
        "id": review["id"],
        "product_id": product_id,
        "user_id": user_id,
        "order_id": order_id,
        "rating": rating,
        "content": content,
        "status": "visible",
        "created_at": review["created_at"],
    }


def get_product_reviews(product_id: int, page: int = 1, size: int = 10) -> tuple:
    """商品评价列表（分页）。"""
    offset = (page - 1) * size

    with get_cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as total FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
        """, (product_id,))
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT r.id, r.user_id, u.nickname,
                   r.rating, r.content, r.created_at
            FROM shop.reviews r
            JOIN shop.users u ON r.user_id = u.id
            WHERE r.product_id = %s AND r.status = 'visible'
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """, (product_id, size, offset))
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    return items, total


def get_review_stats(product_id: int) -> Dict[str, Any]:
    """评价统计。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT COALESCE(AVG(rating), 0) as avg_rating,
                   COUNT(*) as total_count
            FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
        """, (product_id,))
        stats = cur.fetchone()

        cur.execute("""
            SELECT rating, COUNT(*) as count
            FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
            GROUP BY rating
        """, (product_id,))
        rows = cur.fetchall()

    distribution = {str(i): 0 for i in range(1, 6)}
    for row in rows:
        distribution[str(row["rating"])] = row["count"]

    return {
        "avg_rating": round(float(stats["avg_rating"]), 2),
        "total_count": stats["total_count"],
        "distribution": distribution,
    }


def get_user_reviews(user_id: int, page: int = 1, size: int = 10) -> tuple:
    """用户评价列表（分页）。"""
    offset = (page - 1) * size

    with get_cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as total FROM shop.reviews
            WHERE user_id = %s AND status = 'visible'
        """, (user_id,))
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT r.id, r.product_id, p.name as product_name,
                   r.order_id, r.rating, r.content, r.created_at
            FROM shop.reviews r
            JOIN shop.products p ON r.product_id = p.id
            WHERE r.user_id = %s AND r.status = 'visible'
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, size, offset))
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    return items, total


def update_product_rating_cache(product_id: int) -> None:
    """更新商品评分缓存。"""
    cache_key = CACHE_KEY_PRODUCT.format(id=product_id)

    with get_cursor() as cur:
        cur.execute("""
            SELECT COALESCE(AVG(rating), 0) as avg_rating,
                   COUNT(*) as review_count
            FROM shop.reviews
            WHERE product_id = %s AND status = 'visible'
        """, (product_id,))
        stats = cur.fetchone()

        cur.execute("""
            UPDATE shop.products
            SET avg_rating = %s, review_count = %s
            WHERE id = %s
        """, (round(float(stats["avg_rating"]), 2), stats["review_count"], product_id))

    cached = get_cache(cache_key)
    if cached:
        cached["avg_rating"] = round(float(stats["avg_rating"]), 2)
        cached["review_count"] = stats["review_count"]
        set_cache(cache_key, cached, ttl=600)


def get_latest_reviews(product_id: int, limit: int = 10) -> List[Dict]:
    """获取商品最新评价（供 AI 服务调用），附带用户昵称。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT r.id, r.user_id, u.nickname, r.rating, r.content, r.created_at
            FROM shop.reviews r
            JOIN shop.users u ON r.user_id = u.id
            WHERE r.product_id = %s AND r.status = 'visible'
            ORDER BY r.created_at DESC
            LIMIT %s
        """, (product_id, limit))
        rows = cur.fetchall()

    return [dict(row) for row in rows]