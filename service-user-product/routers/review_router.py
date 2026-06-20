"""★ 小B：评价路由 — 商品评价 CRUD + 统计

接口说明：
  - POST /reviews — 创建评价（需登录）
  - GET  /reviews/product/{product_id} — 商品评价列表（公开）
  - GET  /reviews/product/{product_id}/stats — 评价统计（公开）
  - GET  /reviews/user/me — 我的评价（需登录）
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.common.exceptions import BusinessError
from shop_shared.middleware import get_current_user

from services.review_service import (
    create_review,
    get_product_reviews,
    get_review_stats,
    get_user_reviews,
)

router = APIRouter(prefix="/reviews", tags=["评价"])


class CreateReviewRequest(BaseModel):
    product_id: int
    order_id: int
    rating: int
    content: str = ""

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("评分必须在 1-5 之间")
        return v

    @field_validator("product_id", "order_id")
    @classmethod
    def id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ID 必须为正整数")
        return v


@router.post("")
def create_review_endpoint(
    req: CreateReviewRequest,
    user: dict = Depends(get_current_user),
):
    """创建评价（需登录）。"""
    review = create_review(
        user_id=user["user_id"],
        product_id=req.product_id,
        order_id=req.order_id,
        rating=req.rating,
        content=req.content,
    )
    return success_response(review)


@router.get("/product/{product_id}")
def get_product_reviews_endpoint(
    product_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """商品评价列表（公开）。"""
    reviews, total = get_product_reviews(product_id, page, size)
    return success_response({
        "items": reviews,
        "total": total,
        "page": page,
        "size": size,
    })


@router.get("/product/{product_id}/stats")
def get_review_stats_endpoint(product_id: int):
    """评价统计（公开）。"""
    stats = get_review_stats(product_id)
    return success_response(stats)


@router.get("/user/me")
def get_user_reviews_endpoint(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """我的评价（需登录）。"""
    reviews, total = get_user_reviews(user["user_id"], page, size)
    return success_response({
        "items": reviews,
        "total": total,
        "page": page,
        "size": size,
    })