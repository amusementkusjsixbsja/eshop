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
from shop_shared.common.exceptions import NotFoundError
from shop_shared.middleware import get_current_user

router = APIRouter(prefix="/logistics", tags=["物流"])

MOCK_LOGISTICS = {
    1001: {
        "id": 1, "order_id": 1001, "tracking_number": "SF1234567890",
        "carrier": "SF-Express", "status": "in_transit",
        "current_location": "广州市中转中心",
        "estimated_delivery": "2026-06-03T18:00:00",
        "timeline": [
            {"time": "2026-06-01T10:05:00", "status": "已揽件", "location": "深圳市南山营业部"},
            {"time": "2026-06-01T14:30:00", "status": "运输中", "location": "深圳市分拣中心"},
            {"time": "2026-06-02T08:00:00", "status": "运输中", "location": "广州市中转中心"},
        ],
    },
}


@router.get("/{order_id}")
def get_logistics(order_id: int, user: dict = Depends(get_current_user)):
    """查询订单物流状态。"""
    uid = user["user_id"]
    # TODO: 小C — 替换为真实查询
    # SELECT * FROM shop.logistics_records WHERE order_id = %s
    # 同时 JOIN shop.orders 校验 user_id
    logistics = MOCK_LOGISTICS.get(order_id)
    if not logistics:
        return success_response({"message": "物流信息等待更新"})
    return success_response(logistics)
