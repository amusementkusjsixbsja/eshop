"""分类管理业务逻辑。"""

from shop_shared.infrastructure import get_cursor, delete_cache
from shop_shared.common.exceptions import NotFoundError, BusinessError


def get_all_categories() -> list:
    """获取全部分类（扁平列表，按 sort_order 排序）。"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM shop.categories ORDER BY sort_order")
        return cur.fetchall()


def create_category(name: str, parent_id: int | None = None) -> dict:
    """创建分类，返回新分类记录。"""
    with get_cursor() as cur:
        # 如果指定了 parent_id，校验父分类是否存在
        if parent_id is not None:
            cur.execute("SELECT id FROM shop.categories WHERE id = %s", (parent_id,))
            if not cur.fetchone():
                raise NotFoundError("父分类不存在")

        cur.execute(
            "INSERT INTO shop.categories (name, parent_id) VALUES (%s, %s) RETURNING *",
            (name, parent_id),
        )
        row = cur.fetchone()

    delete_cache("categories:tree")
    return row


def update_category(category_id: int, name: str | None = None, parent_id: int | None = None) -> dict:
    """编辑分类，仅更新非 None 字段。"""
    fields, values = [], []
    if name is not None:
        fields.append("name = %s")
        values.append(name)
    if parent_id is not None:
        fields.append("parent_id = %s")
        values.append(parent_id)
    if not fields:
        raise BusinessError("至少需要提供一个更新字段")

    # 如果指定了 parent_id，校验父分类存在且不能把自己设为自己的子分类
    if parent_id is not None:
        if parent_id == category_id:
            raise BusinessError("不能将分类设为自己的子分类")

    values.append(category_id)
    with get_cursor() as cur:
        # 校验父分类
        if parent_id is not None:
            cur.execute("SELECT id FROM shop.categories WHERE id = %s", (parent_id,))
            if not cur.fetchone():
                raise NotFoundError("父分类不存在")

        cur.execute(
            f"UPDATE shop.categories SET {', '.join(fields)} WHERE id = %s RETURNING *",
            tuple(values),
        )
        row = cur.fetchone()

    if not row:
        raise NotFoundError("分类不存在")

    delete_cache("categories:tree")
    return row


def delete_category(category_id: int) -> None:
    """删除分类，有关联商品则拒绝。"""
    with get_cursor() as cur:
        # 1. 检查是否有商品引用此分类
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM shop.products WHERE category_id = %s",
            (category_id,),
        )
        result = cur.fetchone()
        if result["cnt"] > 0:
            raise BusinessError(f"该分类下有 {result['cnt']} 个商品，无法删除")

        # 2. 检查是否有子分类引用
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM shop.categories WHERE parent_id = %s",
            (category_id,),
        )
        child_result = cur.fetchone()
        if child_result["cnt"] > 0:
            raise BusinessError(f"该分类下有 {child_result['cnt']} 个子分类，无法删除")

        # 3. 执行删除
        cur.execute("DELETE FROM shop.categories WHERE id = %s", (category_id,))
        if cur.rowcount == 0:
            raise NotFoundError("分类不存在")

    delete_cache("categories:tree")
