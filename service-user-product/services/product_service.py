"""商品业务逻辑层（含缓存操作）。

★ 小B：商品相关业务逻辑。

参考：
  - shop_shared.infrastructure.database.get_cursor() — 数据库查询
  - shop_shared.infrastructure.redis_client.get_cache() / set_cache() — 缓存
"""

from typing import Any, Dict, List, Optional

from shop_shared.infrastructure.database import get_cursor
from shop_shared.infrastructure.redis_client import get_cache, set_cache


CACHE_KEY_PRODUCT = "product:{id}"
CACHE_KEY_HOT_PRODUCTS = "hot:products:list"


def get_products(
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> Dict[str, Any]:
    """商品列表查询（支持分类筛选、关键词搜索、价格区间、分页）。

    Args:
        category_id: 分类 ID（可选，含子分类）
        keyword: 搜索关键词（可选，匹配 name 或 description）
        page: 页码（从 1 开始）
        size: 每页数量
        min_price: 最低价格（可选）
        max_price: 最高价格（可选）

    Returns:
        包含 items 和 total 的字典
    """
    offset = (page - 1) * size

    with get_cursor() as cur:
        where_clauses = ["p.status = 'on_sale'"]
        params = []

        if category_id:
            # 含子分类：匹配该分类本身，或其直接子分类（分类树为两层）
            where_clauses.append(
                "(p.category_id = %s OR p.category_id IN "
                "(SELECT id FROM shop.categories WHERE parent_id = %s))"
            )
            params.append(category_id)
            params.append(category_id)

        if keyword:
            where_clauses.append("(p.name ILIKE %s OR p.description ILIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        if min_price is not None:
            where_clauses.append("p.price >= %s")
            params.append(min_price)

        if max_price is not None:
            where_clauses.append("p.price <= %s")
            params.append(max_price)

        where_sql = " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) as total FROM shop.products p WHERE {where_sql}"
        cur.execute(count_sql, params)
        total = cur.fetchone()["total"]

        query_sql = f"""
            SELECT p.id, p.name, p.description, p.price, p.image_url,
                   p.stock, p.category_id, c.name as category_name, p.status,
                   p.avg_rating, p.review_count
            FROM shop.products p
            LEFT JOIN shop.categories c ON p.category_id = c.id
            WHERE {where_sql}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])
        cur.execute(query_sql, params)
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    return {"items": items, "total": total}


def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """商品详情查询（Cache-Aside 模式）。

    Args:
        product_id: 商品 ID

    Returns:
        商品信息字典，不存在返回 None
    """
    cache_key = CACHE_KEY_PRODUCT.format(id=product_id)

    cached = get_cache(cache_key)
    if cached:
        return cached

    with get_cursor() as cur:
        cur.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_url,
                   p.stock, p.category_id, c.name as category_name, p.status,
                   p.avg_rating, p.review_count
            FROM shop.products p
            LEFT JOIN shop.categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.status = 'on_sale'
        """, (product_id,))
        row = cur.fetchone()

    if row:
        product = dict(row)
        set_cache(cache_key, product, ttl=600)
        return product

    return None


def get_hot_products(limit: int = 5) -> List[Dict[str, Any]]:
    """热门商品查询（Redis 缓存优先）。

    Args:
        limit: 返回数量，默认 5

    Returns:
        热门商品列表
    """
    cache_key = CACHE_KEY_HOT_PRODUCTS

    cached = get_cache(cache_key)
    if cached:
        return cached[:limit]

    with get_cursor() as cur:
        cur.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image_url,
                   p.stock, p.category_id, c.name as category_name, p.status,
                   p.avg_rating, p.review_count
            FROM shop.products p
            LEFT JOIN shop.categories c ON p.category_id = c.id
            WHERE p.status = 'on_sale'
            ORDER BY p.created_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    if items:
        set_cache(cache_key, items, ttl=300)

    return items


def update_product_stock(product_id: int, quantity: int) -> bool:
    """更新商品库存（减少）。

    Args:
        product_id: 商品 ID
        quantity: 减少的数量

    Returns:
        更新是否成功
    """
    cache_key = CACHE_KEY_PRODUCT.format(id=product_id)

    with get_cursor() as cur:
        cur.execute(
            """UPDATE shop.products
               SET stock = stock - %s
               WHERE id = %s AND stock >= %s
               RETURNING id""",
            (quantity, product_id, quantity)
        )
        row = cur.fetchone()

    if row:
        delete_cache(cache_key)
        return True

    return False


def delete_cache(cache_key: str) -> None:
    """删除缓存。"""
    # Redis 删除缓存操作（如果需要）
    pass
