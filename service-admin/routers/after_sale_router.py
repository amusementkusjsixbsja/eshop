"""★ 小D：售后管理路由（管理后台）。

接口说明：
  - GET    /after-sales          — 全部售后申请（分页，支持按状态筛选）
  - PATCH  /after-sales/{id}/approve — 审核通过
  - PATCH  /after-sales/{id}/reject  — 审核拒绝
"""

from fastapi import APIRouter, Depends, Query

from shop_shared.common import paginated_response, success_response
from shop_shared.middleware import get_current_admin

from services.after_sale_service import (
    list_all_after_sales,
    approve_after_sale,
    reject_after_sale,
)

router = APIRouter(prefix="/after-sales", tags=["管理后台-售后"])


@router.get("")
def list_after_sales(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str = Query(None, regex="^(pending|approved|rejected|completed)?$"),
    admin: dict = Depends(get_current_admin),
):
    """全部售后申请（可按状态筛选）。"""
    result = list_all_after_sales(page=page, size=size, status=status)
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        size=result["size"],
    )


@router.patch("/{after_sale_id}/approve")
def approve_after_sale_handler(after_sale_id: int, admin: dict = Depends(get_current_admin)):
    """审核通过售后申请。"""
    result = approve_after_sale(after_sale_id)
    return success_response(result)


@router.patch("/{after_sale_id}/reject")
def reject_after_sale_handler(after_sale_id: int, admin: dict = Depends(get_current_admin)):
    """审核拒绝售后申请。"""
    result = reject_after_sale(after_sale_id)
    return success_response(result)
