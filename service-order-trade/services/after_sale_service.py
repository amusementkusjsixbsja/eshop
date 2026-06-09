"""售后业务逻辑层。"""

from shop_shared.infrastructure.database import get_cursor
from shop_shared.common.exceptions import BusinessError, NotFoundError


def validate_order_paid(order_id: int, user_id: int) -> dict:
    """校验订单状态为 paid。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, status, user_id FROM shop.orders WHERE id = %s
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise NotFoundError("订单不存在")
        if order["status"] != "paid":
            raise BusinessError("只有已支付的订单才能申请售后")
        return order


def create_after_sale(user_id: int, order_id: int, after_type: str, reason: str) -> dict:
    """申请售后（仅 paid 订单可申请）。"""
    validate_order_paid(order_id, user_id)

    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO shop.after_sale_requests (user_id, order_id, type, reason)
            VALUES (%s, %s, %s, %s)
            RETURNING id, status, created_at
        """, (user_id, order_id, after_type, reason))
        result = cur.fetchone()
        return {
            "id": result["id"],
            "order_id": order_id,
            "type": after_type,
            "reason": reason,
            "status": result["status"],
            "created_at": result["created_at"],
        }


def get_user_after_sales(user_id: int) -> list:
    """查询用户的售后申请列表。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, order_id, type, reason, status, created_at
            FROM shop.after_sale_requests
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        return cur.fetchall()
