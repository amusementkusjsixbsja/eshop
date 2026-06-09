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
from services.after_sale_service import create_after_sale, get_user_after_sales

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


@router.post("")
def create_after_sale_handler(body: AfterSaleRequest, user: dict = Depends(get_current_user)):
    """申请售后（仅 paid 订单可申请）。"""
    uid = user["user_id"]
    result = create_after_sale(uid, body.order_id, body.type, body.reason)
    return success_response(result)


@router.get("")
def list_after_sales_handler(user: dict = Depends(get_current_user)):
    """查询本人的售后申请列表。"""
    uid = user["user_id"]
    items = get_user_after_sales(uid)
    return success_response({"items": items})
