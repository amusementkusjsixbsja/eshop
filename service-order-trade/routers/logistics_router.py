"""★ 小C：物流路由。

接口说明（对照需求文档 §6.2.10）：
  - GET /logistics/{order_id} — 查询物流状态 + 运输节点时间线

关键规则：
  - 仅可查询本人订单的物流
  - 支付成功后自动关联预置物流演示数据
  - 物流状态流转：picked_up → in_transit → out_for_delivery → delivered
"""

from fastapi import APIRouter, Depends

from shop_shared.common import success_response
from shop_shared.middleware import get_current_user
from services.logistics_service import get_logistics_by_order

router = APIRouter(prefix="/logistics", tags=["物流"])


@router.get("/{order_id}")
def get_logistics(order_id: int, user: dict = Depends(get_current_user)):
    """查询订单物流状态。"""
    uid = user["user_id"]
    logistics = get_logistics_by_order(order_id, uid)
    return success_response(logistics)
