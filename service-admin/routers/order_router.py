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
from services.order_service import list_all_orders as svc_list_all_orders
from services.order_service import get_order_detail as svc_get_order_detail

router = APIRouter(prefix="/orders", tags=["订单查看"])


@router.get("")
def list_orders(
    status: str = Query(None, regex="^(pending|paid|cancelled)?$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
):
    """查看全部订单（按时间倒序，可按状态筛选）。"""
    result = svc_list_all_orders(status=status, page=page, size=size)
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        size=result["size"],
    )


@router.get("/{order_id}")
def order_detail(order_id: int, admin: dict = Depends(get_current_admin)):
    """订单详情（含明细）。"""
    order = svc_get_order_detail(order_id)
    return success_response(order)
