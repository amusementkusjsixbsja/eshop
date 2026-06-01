"""内部接口 — 供 AI 客服服务调用。

接口列表：
  - GET /internal/orders             — 查询用户订单
  - GET /internal/orders/{id}        — 查询订单详情
  - GET /internal/logistics          — 查询物流
  - GET /internal/after-sales        — 查询售后
"""

from fastapi import APIRouter, Depends, Query

from shop_shared.common import success_response
from shop_shared.middleware import verify_internal_token

router = APIRouter(tags=["内部接口"], dependencies=[Depends(verify_internal_token)])


@router.get("/orders")
def internal_list_orders(
    user_id: int = Query(..., description="用户 ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询用户订单列表。"""
    # TODO: 小C — SELECT * FROM shop.orders WHERE user_id = %s ORDER BY created_at DESC
    from .order_router import MOCK_ORDERS
    items = [o for o in MOCK_ORDERS if o["user_id"] == user_id]
    return success_response({"items": items, "total": len(items), "page": page, "size": size})


@router.get("/orders/{order_id}")
def internal_get_order(order_id: int):
    """查询订单详情。"""
    # TODO: 小C — SELECT ... JOIN shop.order_items
    from .order_router import MOCK_ORDERS
    order = next((o for o in MOCK_ORDERS if o["id"] == order_id), None)
    if not order:
        from shop_shared.common.exceptions import NotFoundError
        raise NotFoundError("订单不存在")
    return success_response(order)


@router.get("/logistics")
def internal_get_logistics(user_id: int = Query(...)):
    """查询物流信息。"""
    # TODO: 小C — SELECT l.* FROM shop.logistics_records l
    #            JOIN shop.orders o ON l.order_id = o.id
    #            WHERE o.user_id = %s
    from .logistics_router import MOCK_LOGISTICS
    return success_response({"items": list(MOCK_LOGISTICS.values())})


@router.get("/after-sales")
def internal_get_after_sales(user_id: int = Query(...)):
    """查询售后申请。"""
    # TODO: 小C — SELECT * FROM shop.after_sale_requests WHERE user_id = %s
    from .after_sale_router import MOCK_AFTER_SALES
    items = [a for a in MOCK_AFTER_SALES if a["user_id"] == user_id]
    return success_response({"items": items})
