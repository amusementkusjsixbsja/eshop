"""★ 小D：评价管理路由（管理后台）。

接口说明：
  - GET    /reviews                        — 评价列表（分页，支持筛选）
  - GET    /reviews/product/{product_id}   — 某商品评价管理
  - PATCH  /reviews/{review_id}/status     — 隐藏/显示评价
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from shop_shared.common import success_response
from shop_shared.middleware import get_current_admin

from services.review_service import (
    get_all_reviews,
    set_review_status,
    get_product_reviews_for_admin,
)

router = APIRouter(prefix="/reviews", tags=["管理后台-评价"])


class SetReviewStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(visible|hidden)$")


@router.get("")
def list_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    product_id: int = Query(None, description="按商品筛选"),
    rating: int = Query(None, ge=1, le=5, description="按星级筛选"),
    admin: dict = Depends(get_current_admin),
):
    """评价列表（分页，支持按商品/星级筛选）。"""
    items, total = get_all_reviews(page, size, product_id, rating)
    return success_response({"items": items, "total": total, "page": page, "size": size})


@router.get("/product/{product_id}")
def list_product_reviews_admin(
    product_id: int,
    admin: dict = Depends(get_current_admin),
):
    """某商品的全部评价（含隐藏）。"""
    reviews = get_product_reviews_for_admin(product_id)
    return success_response({"items": reviews})


@router.patch("/{review_id}/status")
def update_review_status(
    review_id: int,
    req: SetReviewStatusRequest,
    admin: dict = Depends(get_current_admin),
):
    """隐藏/显示评价。"""
    review = set_review_status(review_id, req.status)
    return success_response(review)
