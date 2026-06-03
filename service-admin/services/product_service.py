"""商品管理业务逻辑。"""

from shop_shared.infrastructure import get_cursor
from shop_shared.infrastructure.redis_client import delete_keys
from shop_shared.common.exceptions import NotFoundError, BusinessError


def list_all_products(status: str | None = None, page: int = 1, size: int = 20) -> tuple:
    """
    管理员视角商品列表（含下架商品）。
    返回: (items, total)
    """
    where_clause = ""
    params: list = []

    if status:
        where_clause = "WHERE p.status = %s"
        params.append(status)

    with get_cursor() as cur:
        # 查总数
        count_sql = f"SELECT COUNT(*) AS total FROM shop.products p {where_clause}"
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()["total"]

        # 查分页数据
        data_sql = f"""
            SELECT p.*, c.name AS category_name
            FROM shop.products p
            LEFT JOIN shop.categories c ON p.category_id = c.id
            {where_clause}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        offset = (page - 1) * size
        cur.execute(data_sql, tuple(params + [size, offset]))
        items = cur.fetchall()

    return items, total


def create_product(data: dict) -> dict:
    """发布商品，初始状态 on_sale。"""
    # 校验分类存在
    with get_cursor() as cur:
        cur.execute("SELECT id FROM shop.categories WHERE id = %s", (data["category_id"],))
        if not cur.fetchone():
            raise NotFoundError("分类不存在")

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO shop.products (name, description, price, image_url, stock, category_id, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'on_sale') RETURNING *""",
            (
                data["name"],
                data.get("description", ""),
                data["price"],
                data.get("image_url", ""),
                data["stock"],
                data["category_id"],
            ),
        )
        row = cur.fetchone()

    delete_keys(["hot:products:list"])
    return row


def update_product(product_id: int, data: dict) -> dict:
    """编辑商品（支持部分更新）。"""
    fields, values = [], []
    for key in ("name", "description", "price", "image_url", "stock", "category_id"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        raise BusinessError("至少需要提供一个更新字段")

    # 校验分类存在（如果要改 category_id）
    if "category_id" in data and data["category_id"] is not None:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM shop.categories WHERE id = %s", (data["category_id"],))
            if not cur.fetchone():
                raise NotFoundError("分类不存在")

    # 自动更新 updated_at
    fields.append("updated_at = NOW()")
    values.append(product_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE shop.products SET {', '.join(fields)} WHERE id = %s RETURNING *",
            tuple(values),
        )
        row = cur.fetchone()

    if not row:
        raise NotFoundError("商品不存在")

    delete_keys([f"product:{product_id}", "hot:products:list"])
    return row


def toggle_product_status(product_id: int, status: str) -> dict:
    """上下架商品。"""
    if status not in ("on_sale", "off_sale"):
        raise BusinessError("状态值无效，只能是 on_sale 或 off_sale")

    with get_cursor() as cur:
        cur.execute(
            "UPDATE shop.products SET status = %s, updated_at = NOW() WHERE id = %s RETURNING *",
            (status, product_id),
        )
        row = cur.fetchone()

    if not row:
        raise NotFoundError("商品不存在")

    delete_keys([f"product:{product_id}", "hot:products:list"])
    return row
