"""★ 小B：商品路由 — 调用 services 层实现。"""

from fastapi import APIRouter, Query

from shop_shared.common import success_response, paginated_response
from shop_shared.common.exceptions import NotFoundError

from services.product_service import (
    get_products,
    get_product_by_id,
    get_hot_products,
)
from services.category_service import get_category_tree

router = APIRouter(prefix="/products", tags=["商品"])


@router.get("")
def list_products(
    category_id: int = Query(None, description="分类 ID"),
    keyword: str = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """商品列表：分类筛选 + 关键词搜索 + 分页。"""
    result = get_products(
        category_id=category_id,
        keyword=keyword,
        page=page,
        size=size
    )
    return paginated_response(result["items"], result["total"], page, size)


@router.get("/hot")
def get_hot():
    """热门商品列表（前 5 条 on_sale 商品）。"""
    items = get_hot_products(limit=5)
    return success_response({"items": items})


@router.get("/{product_id}")
def get_product_detail(product_id: int):
    """商品详情（Cache-Aside 模式）。"""
    product = get_product_by_id(product_id)
    if not product:
        raise NotFoundError("商品不存在")
    return success_response(product)


@router.get("/categories/tree")
def get_categories_tree():
    """分类树（Redis 缓存优先）。"""
    tree = get_category_tree()
    return success_response({"items": tree})
