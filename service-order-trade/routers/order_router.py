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
from shop_shared.common.exceptions import BusinessError
from shop_shared.middleware import get_current_user

router = APIRouter(prefix="/orders", tags=["订单"])


class CreateOrderRequest(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("收货地址不能为空")
        return v.strip()


MOCK_ORDERS = [
    {
        "id": 1001, "user_id": 1, "total_amount": 1798.00, "status": "paid",
        "address": "广东省深圳市南山区", "created_at": "2026-06-01T10:00:00",
        "paid_at": "2026-06-01T10:05:00", "cancelled_at": None,
        "items": [
            {"id": 1, "product_id": 1, "product_name": "智能门锁 X1", "price": 1299.00, "quantity": 1},
            {"id": 2, "product_id": 2, "product_name": "无线耳机 Pro", "price": 499.00, "quantity": 1},
        ],
    },
    {
        "id": 1002, "user_id": 1, "total_amount": 299.00, "status": "pending",
        "address": "广东省深圳市南山区", "created_at": "2026-06-01T11:00:00",
        "paid_at": None, "cancelled_at": None,
        "items": [
            {"id": 3, "product_id": 4, "product_name": "智能音箱", "price": 299.00, "quantity": 1},
        ],
    },
]


@router.post("")
def create_order(body: CreateOrderRequest, user: dict = Depends(get_current_user)):
    """创建订单（同一事务：锁库存 → 扣减 → 创订单 → 清购物车）。

    这是整个系统最核心的业务逻辑。必须保证原子性。

    TODO: 小C — 替换为真实事务逻辑
      事务内（conn.autocommit = False）：
        1. SELECT * FROM shop.cart_items ci JOIN shop.products p ON ci.product_id = p.id
           WHERE ci.user_id = %s — 获取购物车商品 + 当前价格 + 库存
        2. SELECT ... FROM shop.products WHERE id IN (...) FOR UPDATE — 加行级锁
        3. 逐条校验 stock >= quantity — 不足则 ROLLBACK + raise BusinessError
        4. UPDATE shop.products SET stock = stock - quantity WHERE id = %s
        5. INSERT INTO shop.orders (user_id, total_amount, address) RETURNING id
        6. INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity)
           VALUES (...) — 快照
        7. DELETE FROM shop.cart_items WHERE user_id = %s
        8. COMMIT
    """
    uid = user["user_id"]
    # Mock: 直接返回一个订单
    return success_response({
        "id": 2001,
        "total_amount": 1798.00,
        "status": "pending",
        "created_at": "2026-06-01T12:00:00",
    })


@router.get("")
def list_orders(
    status: str = Query(None, regex="^(pending|paid|cancelled)?$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """订单列表（按时间倒序，支持按状态筛选）。"""
    uid = user["user_id"]
    # TODO: 小C — SELECT * FROM shop.orders WHERE user_id = %s ORDER BY created_at DESC
    items = [o for o in MOCK_ORDERS if o["user_id"] == uid]
    if status:
        items = [o for o in items if o["status"] == status]
    return paginated_response(items, len(items), page, size)


@router.get("/{order_id}")
def get_order_detail(order_id: int, user: dict = Depends(get_current_user)):
    """订单详情（含明细）。"""
    uid = user["user_id"]
    # TODO: 小C — SELECT ... JOIN shop.order_items WHERE id = %s AND user_id = %s
    order = next((o for o in MOCK_ORDERS if o["id"] == order_id and o["user_id"] == uid), None)
    if not order:
        from shop_shared.common.exceptions import NotFoundError
        raise NotFoundError("订单不存在")
    return success_response(order)


@router.post("/{order_id}/pay")
def pay_order(order_id: int, user: dict = Depends(get_current_user)):
    """模拟支付（幂等：FOR UPDATE + 状态校验）。

    TODO: 小C — 替换为真实逻辑
      事务内：
        1. SELECT ... FROM shop.orders WHERE id = %s FOR UPDATE
        2. 校验 status = pending，否则 raise BusinessError(已支付 / 已取消)
        3. UPDATE shop.orders SET status = 'paid', paid_at = NOW()
        4. INSERT INTO shop.payment_records (order_id, amount, method='mock')
        5. 自动关联物流演示数据
        6. COMMIT
    """
    return success_response({
        "id": order_id,
        "status": "paid",
        "paid_at": "2026-06-01T12:05:00",
    })


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, user: dict = Depends(get_current_user)):
    """取消订单（回滚库存）。

    TODO: 小C — 替换为真实逻辑
      事务内：
        1. SELECT ... FROM shop.orders WHERE id = %s FOR UPDATE
        2. 校验 status = pending，否则 raise BusinessError
        3. UPDATE shop.orders SET status = 'cancelled', cancelled_at = NOW()
        4. 逐条 UPDATE shop.products SET stock = stock + quantity（按 order_items 回滚）
        5. COMMIT
    """
    return success_response({
        "id": order_id,
        "status": "cancelled",
        "cancelled_at": "2026-06-01T12:10:00",
    })
