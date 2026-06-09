"""★ 小D：分类管理路由。

接口说明（对照需求文档 §6.3.1）：
  - GET    /categories       — 全部分类列表（扁平，含 parent_id）
  - POST   /categories       — 创建分类（支持二级：parent_id 可选）
  - PUT    /categories/{id}  — 编辑分类（名称、父级）
  - DELETE /categories/{id}  — 删除分类（检查商品引用，有引用则拒绝）

关键规则：
  - 增删改后需删除 Redis key: categories:tree
  - 删除时检查 shop.products 中是否有关联
  - 所有操作需要 role=admin
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shop_shared.common import success_response
from shop_shared.middleware import get_current_admin
from services.category_service import (
    get_all_categories,
    create_category as svc_create_category,
    update_category as svc_update_category,
    delete_category as svc_delete_category,
)

router = APIRouter(prefix="/categories", tags=["分类管理"])


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: int | None = None


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    parent_id: int | None = None


@router.get("")
def list_categories(admin: dict = Depends(get_current_admin)):
    """全部分类列表。"""
    items = get_all_categories()
    return success_response({"items": items})


@router.post("")
def create_category(body: CreateCategoryRequest, admin: dict = Depends(get_current_admin)):
    """创建分类。"""
    row = svc_create_category(body.name, body.parent_id)
    return success_response(row)


@router.put("/{category_id}")
def update_category(category_id: int, body: UpdateCategoryRequest, admin: dict = Depends(get_current_admin)):
    """编辑分类。"""
    row = svc_update_category(category_id, body.name, body.parent_id)
    return success_response(row)


@router.delete("/{category_id}")
def delete_category(category_id: int, admin: dict = Depends(get_current_admin)):
    """删除分类（有商品引用则拒绝）。"""
    svc_delete_category(category_id)
    return success_response({"message": "删除成功"})
