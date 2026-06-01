"""★ 小D：商品管理路由。

接口说明（对照需求文档 §6.3.2）：
  - GET    /products               — 全部商品列表（含下架商品，管理员视角）
  - POST   /products               — 发布商品（初始 status=on_sale）
  - PUT    /products/{id}           — 编辑商品信息
  - PATCH  /products/{id}/status    — 上下架操作

关键规则：
  - 发布/编辑/上下架后需删除 Redis 缓存:
    - product:{id}（商品详情）
    - hot:products:list（热门商品列表）
  - 下架商品不影响已有订单（订单明细是快照）
  - 所有操作需要 role=admin
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shop_shared.common import success_response, paginated_response
from shop_shared.middleware import get_current_admin

router = APIRouter(prefix="/products", tags=["商品管理"])


class CreateProductRequest(BaseModel):
    name: str
    description: str = ""
    price: float
    image_url: str = ""
    stock: int
    category_id: int


class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    image_url: str | None = None
    stock: int | None = None
    category_id: int | None = None


class StatusRequest(BaseModel):
    status: str  # "on_sale" | "off_sale"


@router.get("")
def list_all_products(
    status: str = None,
    page: int = 1,
    size: int = 20,
    admin: dict = Depends(get_current_admin),
):
    """全部商品列表（管理员视角，包含下架商品）。"""
    # TODO: 小D — SELECT p.*, c.name as category_name FROM shop.products p
    #        JOIN shop.categories c ON p.category_id = c.id
    #        ORDER BY p.created_at DESC
    return paginated_response([], 0, page, size)


@router.post("")
def create_product(body: CreateProductRequest, admin: dict = Depends(get_current_admin)):
    """发布商品。"""
    # TODO: 小D —
    # 1. INSERT INTO shop.products (...) RETURNING id
    # 2. delete_cache("hot:products:list")
    return success_response({
        "id": 100,
        "name": body.name,
        "status": "on_sale",
    })


@router.put("/{product_id}")
def update_product(product_id: int, body: UpdateProductRequest, admin: dict = Depends(get_current_admin)):
    """编辑商品信息。"""
    # TODO: 小D —
    # 1. UPDATE shop.products SET ... WHERE id = %s
    # 2. delete_cache(f"product:{product_id}")
    # 3. delete_cache("hot:products:list")
    return success_response({"id": product_id, "message": "更新成功"})


@router.patch("/{product_id}/status")
def toggle_product_status(product_id: int, body: StatusRequest, admin: dict = Depends(get_current_admin)):
    """上下架商品。"""
    # TODO: 小D —
    # 1. UPDATE shop.products SET status = %s WHERE id = %s
    # 2. delete_cache(f"product:{product_id}")
    # 3. delete_cache("hot:products:list")
    return success_response({
        "id": product_id,
        "status": body.status,
    })
