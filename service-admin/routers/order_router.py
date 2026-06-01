"""★ 小D：订单查看路由（只读）。

接口说明（对照需求文档 §6.3.3）：
  - GET /orders        — 查看全部订单（可按状态筛选）
  - GET /orders/{id}   — 订单详情

关键规则：
  - 管理员可查看所有用户订单，但不可修改（只读）
  - 返回格式与 C 端一致
"""

from fastapi import APIRouter, Depends, Query

from shop_shared.common import paginated_response, success_response
from shop_shared.middleware import get_current_admin

router = APIRouter(prefix="/orders", tags=["订单查看"])


@router.get("")
def list_all_orders(
    status: str = Query(None, regex="^(pending|paid|cancelled)?$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
):
    """查看全部订单（按时间倒序，可按状态筛选）。"""
    # TODO: 小D — SELECT * FROM shop.orders ORDER BY created_at DESC
    return paginated_response([], 0, page, size)


@router.get("/{order_id}")
def get_order_detail(order_id: int, admin: dict = Depends(get_current_admin)):
    """订单详情（含明细）。"""
    # TODO: 小D — SELECT ... JOIN shop.order_items WHERE id = %s
    from shop_shared.common.exceptions import NotFoundError
    raise NotFoundError("订单不存在")
