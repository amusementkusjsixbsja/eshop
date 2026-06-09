"""内部接口 — 供 AI 客服服务调用。

接口列表：
  - GET /internal/orders             — 查询用户订单
  - GET /internal/orders/{id}        — 查询订单详情
  - GET /internal/logistics          — 查询物流
  - GET /internal/after-sales        — 查询售后
"""

import json

from fastapi import APIRouter, Depends, Query

from shop_shared.common import success_response
from shop_shared.middleware import verify_internal_token
from shop_shared.common.exceptions import NotFoundError

from services.order_service import get_user_orders, get_order_detail
from services.logistics_service import get_logistics_by_order
from services.after_sale_service import get_user_after_sales
from shop_shared.infrastructure.database import get_cursor

router = APIRouter(tags=["内部接口"], dependencies=[Depends(verify_internal_token)])


@router.get("/orders")
def internal_list_orders(
    user_id: int = Query(..., description="用户 ID"),
    status: str = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """查询用户订单列表。"""
    items, total = get_user_orders(user_id, status, page, size)
    return success_response({"items": items, "total": total, "page": page, "size": size})


@router.get("/orders/{order_id}")
def internal_get_order(order_id: int):
    """查询订单详情（含明细）。"""
    # 内部接口不校验 user_id，只需要订单存在即可
    with get_cursor() as cur:
        cur.execute("""
            SELECT o.*, array_agg(oi) as items
            FROM shop.orders o
            LEFT JOIN shop.order_items oi ON o.id = oi.order_id
            WHERE o.id = %s
            GROUP BY o.id
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        return success_response(order)


@router.get("/logistics")
def internal_get_logistics(user_id: int = Query(..., description="用户 ID")):
    """查询用户所有物流信息。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT lr.*
            FROM shop.logistics_records lr
            JOIN shop.orders o ON lr.order_id = o.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        items = []
        for r in rows:
            item = dict(r)
            if isinstance(item.get("timeline"), str):
                item["timeline"] = json.loads(item["timeline"])
            items.append(item)
        return success_response({"items": items})


@router.get("/after-sales")
def internal_get_after_sales(user_id: int = Query(..., description="用户 ID")):
    """查询用户售后申请。"""
    items = get_user_after_sales(user_id)
    return success_response({"items": items})
