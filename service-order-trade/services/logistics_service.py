"""物流业务逻辑层。"""

import json

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
        row = cur.fetchone()
        if not row:
            raise NotFoundError("物流信息不存在")
        logistics = dict(row)
        # timeline 以 JSON 字符串存储，需解析为数组
        if isinstance(logistics.get("timeline"), str):
            logistics["timeline"] = json.loads(logistics["timeline"])
        return logistics
