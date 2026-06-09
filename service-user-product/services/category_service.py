"""分类业务逻辑层。

★ 小B：分类树的读取逻辑。

注意：分类的 CRUD 由 service-admin（小D）负责，
本服务只读不写。如需写操作，调用相应数据库语句。

参考：
  - shop_shared.infrastructure.database.get_cursor() — 数据库查询
  - shop_shared.infrastructure.redis_client.get_cache() / set_cache() — 缓存
"""

from typing import Dict, List, Optional

from shop_shared.infrastructure.database import get_cursor
from shop_shared.infrastructure.redis_client import get_cache, set_cache


CACHE_KEY_CATEGORIES_TREE = "categories:tree"
CACHE_KEY_CATEGORY_BY_ID = "category:{id}"


def get_category_tree() -> List[Dict[str, any]]:
    """获取分类树形结构（Redis 缓存优先）。

    Returns:
        分类树形结构列表
    """
    cache_key = CACHE_KEY_CATEGORIES_TREE

    cached = get_cache(cache_key)
    if cached:
        return cached

    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, parent_id, sort_order
            FROM shop.categories
            ORDER BY parent_id NULLS FIRST, sort_order, id
        """)
        rows = cur.fetchall()

    categories = [dict(row) for row in rows]

    tree = []
    children_map = {}

    for cat in categories:
        cat["children"] = []
        children_map[cat["id"]] = cat

    for cat in categories:
        if cat["parent_id"] is None:
            tree.append(cat)
        else:
            parent = children_map.get(cat["parent_id"])
            if parent:
                parent["children"].append(cat)

    if tree:
        set_cache(cache_key, tree, ttl=1800)

    return tree


def get_category_by_id(category_id: int) -> Optional[Dict[str, any]]:
    """根据分类 ID 获取分类信息（Redis 缓存优先）。

    Args:
        category_id: 分类 ID

    Returns:
        分类信息字典，不存在返回 None
    """
    cache_key = CACHE_KEY_CATEGORY_BY_ID.format(id=category_id)

    cached = get_cache(cache_key)
    if cached:
        return cached

    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, parent_id, sort_order
            FROM shop.categories
            WHERE id = %s
        """, (category_id,))
        row = cur.fetchone()

    if row:
        category = dict(row)
        set_cache(cache_key, category, ttl=600)
        return category

    return None


def get_all_categories() -> List[Dict[str, any]]:
    """获取所有分类（平铺列表，带层级信息）。

    Returns:
        分类列表
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, parent_id, sort_order
            FROM shop.categories
            ORDER BY parent_id NULLS FIRST, sort_order, id
        """)
        rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_category_children(parent_id: int) -> List[Dict[str, any]]:
    """获取指定分类的子分类。

    Args:
        parent_id: 父分类 ID

    Returns:
        子分类列表
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, parent_id, sort_order
            FROM shop.categories
            WHERE parent_id = %s
            ORDER BY sort_order, id
        """, (parent_id,))
        rows = cur.fetchall()

    return [dict(row) for row in rows]


def invalidate_category_cache() -> None:
    """使分类缓存失效（当分类数据更新时调用）。"""
    # 删除相关缓存
    # 注意：这里需要实际的 Redis 删除操作
    pass
