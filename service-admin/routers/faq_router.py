"""★ 小D：FAQ 知识库管理路由（管理后台）。

接口说明：
  - GET    /faq          — FAQ 列表
  - POST   /faq          — 添加 FAQ
  - PUT    /faq/{faq_id}  — 修改 FAQ
  - DELETE /faq/{faq_id}  — 删除 FAQ
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from shop_shared.common import success_response
from shop_shared.middleware import get_current_admin

from services.faq_admin_service import (
    get_all_faqs,
    add_faq,
    update_faq,
    delete_faq,
)

router = APIRouter(prefix="/faq", tags=["管理后台-FAQ"])


class AddFaqRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="general", max_length=50)


class UpdateFaqRequest(BaseModel):
    question: str | None = Field(None, min_length=1, max_length=500)
    answer: str | None = Field(None, min_length=1, max_length=2000)
    category: str | None = Field(None, max_length=50)


@router.get("")
def list_faqs(
    category: str = Query(None, description="按分类筛选"),
    admin: dict = Depends(get_current_admin),
):
    """FAQ 列表（支持按分类筛选）。"""
    faqs = get_all_faqs(category)
    return success_response({"items": faqs})


@router.post("")
def create_faq(
    req: AddFaqRequest,
    admin: dict = Depends(get_current_admin),
):
    """添加 FAQ 条目。"""
    faq = add_faq(req.question, req.answer, req.category)
    return success_response(faq)


@router.put("/{faq_id}")
def edit_faq(
    faq_id: int,
    req: UpdateFaqRequest,
    admin: dict = Depends(get_current_admin),
):
    """修改 FAQ（支持部分更新）。"""
    faq = update_faq(faq_id, req.question, req.answer, req.category)
    return success_response(faq)


@router.delete("/{faq_id}")
def remove_faq(
    faq_id: int,
    admin: dict = Depends(get_current_admin),
):
    """删除 FAQ 条目。"""
    delete_faq(faq_id)
    return success_response({"deleted": True})
