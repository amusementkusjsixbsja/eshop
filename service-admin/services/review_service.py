"""★ 小D：评价管理业务逻辑（管理员视角）。

功能：
  - 查看全部评价（含隐藏，支持按商品/星级筛选 + 分页）
  - 隐藏/显示评价（同步更新 products 评分缓存）
  - 查看某商品的全部评价（含隐藏）
"""

from shop_shared.infrastructure import get_cursor
from shop_shared.common.exceptions import NotFoundError, BusinessError


def get_all_reviews(
    page: int = 1,
    size: int = 20,
    product_id: int | None = None,
    rating: int | None = None,
) -> tuple[list, int]:
    """管理员视角评价列表（含隐藏评价），支持筛选 + 分页。

    Args:
        page: 页码（从 1 开始）
        size: 每页数量
        product_id: 按商品筛选（可选）
        rating: 按星级筛选（可选）

    Returns:
        (items, total)
    """
    conditions = []
    params: list = []

    if product_id is not None:
        conditions.append("r.product_id = %s")
        params.append(product_id)
    if rating is not None:
        conditions.append("r.rating = %s")
        params.append(rating)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    offset = (page - 1) * size

    with get_cursor() as cur:
        # 总数
        cur.execute(
            f"SELECT COUNT(*) AS cnt FROM shop.reviews r {where}",
            params,
        )
        total = cur.fetchone()["cnt"]

        # 分页列表（JOIN products + users 取名称）
        cur.execute(
            f"""
            SELECT r.*, p.name AS product_name, u.nickname AS user_nickname
            FROM shop.reviews r
            LEFT JOIN shop.products p ON r.product_id = p.id
            LEFT JOIN shop.users u ON r.user_id = u.id
            {where}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [size, offset],
        )
        items = cur.fetchall()

    return items, total


def set_review_status(review_id: int, status: str) -> dict:
    """隐藏/显示评价（visible ↔ hidden）。

    同步更新 shop.products 的 avg_rating 和 review_count
    （只统计 status='visible' 的评价）。
    """
    if status not in ("visible", "hidden"):
        raise BusinessError("状态值必须为 visible 或 hidden")

    with get_cursor() as cur:
        cur.execute(
            """UPDATE shop.reviews
               SET status = %s, updated_at = NOW()
               WHERE id = %s
               RETURNING id, product_id, user_id, order_id, rating, content, status, created_at, updated_at""",
            [status, review_id],
        )
        review = cur.fetchone()
        if not review:
            raise NotFoundError("评价不存在")

        # 同步更新商品评分缓存（只算 visible 评价）
        cur.execute(
            """UPDATE shop.products
               SET avg_rating = (
                   SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0)
                   FROM shop.reviews
                   WHERE product_id = %s AND status = 'visible'
               ),
               review_count = (
                   SELECT COUNT(*)
                   FROM shop.reviews
                   WHERE product_id = %s AND status = 'visible'
               ),
               updated_at = NOW()
               WHERE id = %s""",
            [review["product_id"], review["product_id"], review["product_id"]],
        )

    return review


def get_product_reviews_for_admin(product_id: int) -> list:
    """获取某商品的全部评价（管理后台，含隐藏评价）。"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT r.*, u.nickname AS user_nickname
               FROM shop.reviews r
               LEFT JOIN shop.users u ON r.user_id = u.id
               WHERE r.product_id = %s
               ORDER BY r.created_at DESC""",
            [product_id],
        )
        return cur.fetchall()
