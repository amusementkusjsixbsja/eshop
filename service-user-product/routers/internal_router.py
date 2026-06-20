"""内部接口 — 供 AI 客服服务调用（认证明文: X-Internal-Token）。

接口列表（对照技术方案第八章）：
  - GET /internal/users/{user_id}     — 查询用户信息
  - GET /internal/products/search     — 搜索商品
  - GET /internal/products/{id}      — 商品详情
"""

from fastapi import APIRouter, Depends, Query

from shop_shared.common import success_response
from shop_shared.common.exceptions import NotFoundError
from shop_shared.middleware import verify_internal_token

from services.user_service import get_user_by_id
from services.product_service import get_products, get_product_by_id
from services.review_service import get_latest_reviews, get_review_stats

router = APIRouter(tags=["内部接口"], dependencies=[Depends(verify_internal_token)])


@router.get("/users/{user_id}")
def get_user(user_id: int):
    """查询用户基本信息。"""
    user = get_user_by_id(user_id)
    if not user:
        raise NotFoundError("用户不存在")
    return success_response(user)


@router.get("/products/search")
def search_products(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """内部接口：搜索商品。"""
    result = get_products(keyword=keyword, page=page, size=size)
    return success_response(result)


@router.get("/products/{product_id}")
def get_product(product_id: int):
    """内部接口：商品详情。"""
    product = get_product_by_id(product_id)
    if not product:
        raise NotFoundError("商品不存在")
    return success_response(product)


@router.get("/reviews/product/{product_id}")
def get_product_reviews_internal(
    product_id: int,
    limit: int = Query(10, ge=1, le=50),
):
    """内部接口：商品最新评价（供AI服务调用）。"""
    reviews = get_latest_reviews(product_id, limit)
    return success_response(reviews)


@router.get("/reviews/product/{product_id}/stats")
def get_product_review_stats_internal(product_id: int):
    """内部接口：评价统计（供AI服务调用）。"""
    stats = get_review_stats(product_id)
    return success_response(stats)
