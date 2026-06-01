"""★ 小C：购物车路由 — 将此文件的 mock 数据替换为真实数据库查询。

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


MOCK_CART = {
    1: [  # user_id=1 的购物车
        {"id": 1, "product_id": 1, "name": "智能门锁 X1", "price": 1299.00, "quantity": 1, "stock": 100},
        {"id": 2, "product_id": 2, "name": "无线耳机 Pro", "price": 499.00, "quantity": 2, "stock": 200},
    ]
}


@router.get("")
def get_cart(user: dict = Depends(get_current_user)):
    """查看购物车。"""
    uid = user["user_id"]
    # TODO: 小C — 替换为真实查询
    # SELECT ci.*, p.name, p.price, p.stock
    # FROM shop.cart_items ci
    # JOIN shop.products p ON ci.product_id = p.id
    # WHERE ci.user_id = %s
    items = MOCK_CART.get(uid) or MOCK_CART.get(1, [])
    return success_response({"items": items})


@router.post("")
def add_to_cart(body: AddCartRequest, user: dict = Depends(get_current_user)):
    """添加购物车（同商品自动叠加数量）。"""
    # TODO: 小C — 替换为真实 UPSERT 逻辑
    # INSERT INTO shop.cart_items (user_id, product_id, quantity)
    # VALUES (%s, %s, %s)
    # ON CONFLICT (user_id, product_id) DO UPDATE
    # SET quantity = shop.cart_items.quantity + EXCLUDED.quantity
    # RETURNING id, product_id, quantity
    return success_response({
        "id": 1,
        "product_id": body.product_id,
        "quantity": body.quantity,
    })


@router.put("/{product_id}")
def update_cart_item(product_id: int, body: UpdateCartRequest, user: dict = Depends(get_current_user)):
    """修改购物车项数量。"""
    # TODO: 小C — UPDATE shop.cart_items SET quantity = %s WHERE user_id = %s AND product_id = %s
    return success_response({
        "product_id": product_id,
        "quantity": body.quantity,
    })


@router.delete("/{product_id}")
def delete_cart_item(product_id: int, user: dict = Depends(get_current_user)):
    """删除购物车项。"""
    # TODO: 小C — DELETE FROM shop.cart_items WHERE user_id = %s AND product_id = %s
    return success_response({"message": "删除成功"})
