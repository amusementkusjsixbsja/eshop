"""★ 小D：订单查看业务逻辑层（只读）。"""

from shop_shared.infrastructure import get_cursor
from shop_shared.common.exceptions import NotFoundError


def list_all_orders(
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    """查看全部订单（按时间倒序，可按状态筛选）。

    Returns:
        {"items": [...], "total": int, "page": int, "size": int}
    """
    offset = (page - 1) * size

    with get_cursor() as cur:
        # —— 基础 SQL：JOIN 用户表取昵称 ——
        if status:
            cur.execute(
                """
                SELECT COUNT(*) as total
                FROM shop.orders o
                LEFT JOIN shop.users u ON o.user_id = u.id
                WHERE o.status = %s
                """,
                [status],
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*) as total
                FROM shop.orders o
                LEFT JOIN shop.users u ON o.user_id = u.id
                """
            )
        total = cur.fetchone()["total"]

        # 查列表
        if status:
            cur.execute(
                """
                SELECT o.id, o.user_id, u.nickname AS user_nickname,
                       o.total_amount, o.status, o.address,
                       o.created_at, o.paid_at, o.cancelled_at
                FROM shop.orders o
                LEFT JOIN shop.users u ON o.user_id = u.id
                WHERE o.status = %s
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
                """,
                [status, size, offset],
            )
        else:
            cur.execute(
                """
                SELECT o.id, o.user_id, u.nickname AS user_nickname,
                       o.total_amount, o.status, o.address,
                       o.created_at, o.paid_at, o.cancelled_at
                FROM shop.orders o
                LEFT JOIN shop.users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
                """,
                [size, offset],
            )
        items = cur.fetchall()

    return {"items": items, "total": total, "page": page, "size": size}


def get_order_detail(order_id: int) -> dict:
    """订单详情（含明细）。

    Returns:
        订单主信息 + items 子列表
    """
    with get_cursor() as cur:
        # 1. 查订单主表
        cur.execute(
            """
            SELECT o.id, o.user_id, u.nickname AS user_nickname,
                   o.total_amount, o.status, o.address,
                   o.created_at, o.paid_at, o.cancelled_at
            FROM shop.orders o
            LEFT JOIN shop.users u ON o.user_id = u.id
            WHERE o.id = %s
            """,
            [order_id],
        )
        order = cur.fetchone()

        if not order:
            raise NotFoundError("订单不存在")

        # 2. 查订单明细
        cur.execute(
            """
            SELECT id, order_id, product_id, product_name, price, quantity, created_at
            FROM shop.order_items
            WHERE order_id = %s
            ORDER BY id
            """,
            [order_id],
        )
        items = cur.fetchall()

    # 3. 组装返回
    order["items"] = items
    return order
