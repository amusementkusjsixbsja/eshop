"""★ 小C：订单路由 — 最核心的业务逻辑。

接口说明（对照需求文档 §6.2.6-§6.2.9，第十章状态机）：
  - POST   /orders          — 创建订单（事务：锁库存→扣减→创订单→清购物车）
  - GET    /orders          — 订单列表（按状态筛选，时间倒序）
  - GET    /orders/{id}     — 订单详情（含 order_items 明细）
  - POST   /orders/{id}/pay — 支付（FOR UPDATE 幂等校验）
  - POST   /orders/{id}/cancel — 取消（FOR UPDATE + 回滚库存）

关键规则：
  - pending → paid / cancelled（不可逆）
  - paid → cancelled ❌ 禁止（本期不做退款）
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response, paginated_response
from shop_shared.middleware import get_current_user
from services.order_service import (
    create_order,
    get_user_orders,
    get_order_detail,
    pay_order,
    cancel_order,
    initiate_payment,
    get_payment_status,
)

router = APIRouter(prefix="/orders", tags=["订单"])


class CreateOrderRequest(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("收货地址不能为空")
        return v.strip()


class PayOrderRequest(BaseModel):
    payment_method: str = "mock"


@router.post("")
def create_order_handler(body: CreateOrderRequest, user: dict = Depends(get_current_user)):
    """创建订单（同一事务：锁库存 → 扣减 → 创订单 → 清购物车）。"""
    uid = user["user_id"]
    result = create_order(uid, body.address)
    return success_response(result)


@router.get("")
def list_orders(
    status: str = Query(None, regex="^(pending|paid|cancelled)?$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """订单列表（按时间倒序，支持按状态筛选）。"""
    uid = user["user_id"]
    orders, total = get_user_orders(uid, status, page, size)
    return paginated_response(orders, total, page, size)


@router.get("/{order_id}")
def get_order_detail_handler(order_id: int, user: dict = Depends(get_current_user)):
    """订单详情（含明细）。"""
    uid = user["user_id"]
    order = get_order_detail(order_id, uid)
    return success_response(order)


@router.post("/{order_id}/pay")
def pay_order_handler(order_id: int, body: PayOrderRequest, user: dict = Depends(get_current_user)):
    """发起支付（返回 processing 状态，前端需轮询 /orders/{id}/payment 获取结果）。"""
    uid = user["user_id"]
    result = initiate_payment(order_id, uid, body.payment_method)
    return success_response(result)


@router.get("/{order_id}/payment")
def get_payment_status_handler(order_id: int, user: dict = Depends(get_current_user)):
    """查询支付状态（供前端轮询）。"""
    uid = user["user_id"]
    result = get_payment_status(order_id, uid)
    return success_response(result)


@router.post("/{order_id}/cancel")
def cancel_order_handler(order_id: int, user: dict = Depends(get_current_user)):
    """取消订单（回滚库存）。"""
    uid = user["user_id"]
    result = cancel_order(order_id, uid)
    return success_response(result)
