"""★ 小C：售后路由。

接口说明（对照需求文档 §6.2.11）：
  - POST /after-sales  — 申请售后（仅 paid 订单可申请）
  - GET  /after-sales  — 查询本人的售后申请列表

关键规则：
  - type: refund(退款) / return(退货) — exchange(换货 P1 保留不实现)
  - status: pending → approved → completed / pending → rejected
  - P0 只实现"申请"和"查询"，管理员审核为 P1
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.middleware import get_current_user

router = APIRouter(prefix="/after-sales", tags=["售后"])


class AfterSaleRequest(BaseModel):
    order_id: int
    type: str
    reason: str = ""

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("refund", "return"):
            raise ValueError("售后类型必须为 refund(退款) 或 return(退货)")
        return v


MOCK_AFTER_SALES = [
    {
        "id": 1, "order_id": 1001, "user_id": 1,
        "type": "refund", "reason": "商品质量问题",
        "status": "approved", "created_at": "2026-06-01T10:30:00",
    },
]


@router.post("")
def create_after_sale(body: AfterSaleRequest, user: dict = Depends(get_current_user)):
    """申请售后。"""
    # TODO: 小C — INSERT INTO shop.after_sale_requests (user_id, order_id, type, reason)
    # 前置条件：校验订单状态为 paid
    return success_response({
        "id": 2,
        "status": "pending",
    })


@router.get("")
def list_after_sales(user: dict = Depends(get_current_user)):
    """查询本人的售后申请列表。"""
    uid = user["user_id"]
    # TODO: 小C — SELECT * FROM shop.after_sale_requests WHERE user_id = %s ORDER BY created_at DESC
    return success_response({
        "items": [a for a in MOCK_AFTER_SALES if a["user_id"] == uid],
    })
