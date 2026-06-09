"""购物车路由。

接口说明（对照需求文档 §6.2.5）：
  - GET    /cart         — 查看购物车（JOIN products 获取名称/价格/库存）
  - POST   /cart         — 添加购物车（UPSERT 幂等叠加数量）
  - PUT    /cart/{id}    — 修改数量
  - DELETE /cart/{id}    — 删除购物车项
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.middleware import get_current_user
from services.cart_service import (
    get_cart_items,
    add_to_cart,
    update_cart_quantity,
    delete_cart_item,
)

router = APIRouter(prefix="/cart", tags=["购物车"])


class AddCartRequest(BaseModel):
    product_id: int
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("数量必须大于 0")
        return v


class UpdateCartRequest(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("数量必须大于 0")
        return v


@router.get("")
def get_cart(user: dict = Depends(get_current_user)):
    """查看购物车。"""
    uid = user["user_id"]
    items = get_cart_items(uid)
    return success_response({"items": items})


@router.post("")
def add_to_cart_handler(body: AddCartRequest, user: dict = Depends(get_current_user)):
    """添加购物车（同商品自动叠加数量）。"""
    uid = user["user_id"]
    result = add_to_cart(uid, body.product_id, body.quantity)
    return success_response(result)


@router.put("/{product_id}")
def update_cart_item(product_id: int, body: UpdateCartRequest, user: dict = Depends(get_current_user)):
    """修改购物车项数量。"""
    uid = user["user_id"]
    result = update_cart_quantity(uid, product_id, body.quantity)
    return success_response(result)


@router.delete("/{product_id}")
def delete_cart_item_handler(product_id: int, user: dict = Depends(get_current_user)):
    """删除购物车项。"""
    uid = user["user_id"]
    delete_cart_item(uid, product_id)
    return success_response({"message": "删除成功"})
