"""物流业务逻辑层。"""

from shop_shared.infrastructure.database import get_cursor
from shop_shared.common.exceptions import NotFoundError


def get_logistics_by_order(order_id: int, user_id: int) -> dict:
    """根据订单ID查询物流信息（校验订单归属）。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT lr.* 
            FROM shop.logistics_records lr
            JOIN shop.orders o ON lr.order_id = o.id
            WHERE lr.order_id = %s AND o.user_id = %s
        """, (order_id, user_id))
        logistics = cur.fetchone()
        if not logistics:
            raise NotFoundError("物流信息不存在")
        return logistics
