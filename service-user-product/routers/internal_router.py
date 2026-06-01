"""内部接口 — 供 AI 客服服务调用（认证明文: X-Internal-Token）。

接口列表（对照技术方案第八章）：
  - GET /internal/users/{user_id}     — 查询用户信息
  - GET /internal/products/search     — 搜索商品
  - GET /internal/products/{id}       — 商品详情
"""

from fastapi import APIRouter, Depends, Query

from shop_shared.common import success_response
from shop_shared.middleware import verify_internal_token

router = APIRouter(tags=["内部接口"], dependencies=[Depends(verify_internal_token)])


@router.get("/users/{user_id}")
def get_user(user_id: int):
    """查询用户基本信息。"""
    # TODO: 小B — SELECT id, email, nickname FROM shop.users WHERE id = %s
    return success_response({
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "nickname": f"用户{user_id}",
    })


@router.get("/products/search")
def search_products(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """内部接口：搜索商品。"""
    # TODO: 小B — SELECT ... FROM shop.products WHERE name ILIKE %s AND status = 'on_sale'
    from .product_router import MOCK_PRODUCTS
    matched = [p for p in MOCK_PRODUCTS if keyword.lower() in p["name"].lower() and p["status"] == "on_sale"]
    return success_response({
        "items": matched[:size],
        "total": len(matched),
        "page": page,
        "size": size,
    })


@router.get("/products/{product_id}")
def get_product(product_id: int):
    """内部接口：商品详情。"""
    # TODO: 小B — SELECT ... FROM shop.products WHERE id = %s
    from .product_router import MOCK_PRODUCTS
    product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
    if not product:
        from shop_shared.common.exceptions import NotFoundError
        raise NotFoundError("商品不存在")
    return success_response(product)
