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

router = APIRouter(prefix="/categories", tags=["分类管理"])


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: int | None = None


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    parent_id: int | None = None


MOCK_CATEGORIES = [
    {"id": 1, "name": "智能家居", "parent_id": None, "sort_order": 1},
    {"id": 2, "name": "数码配件", "parent_id": None, "sort_order": 2},
    {"id": 3, "name": "安防设备", "parent_id": None, "sort_order": 3},
    {"id": 10, "name": "智能门锁", "parent_id": 1, "sort_order": 1},
    {"id": 11, "name": "智能照明", "parent_id": 1, "sort_order": 2},
    {"id": 20, "name": "耳机", "parent_id": 2, "sort_order": 1},
    {"id": 21, "name": "充电设备", "parent_id": 2, "sort_order": 2},
    {"id": 30, "name": "摄像头", "parent_id": 3, "sort_order": 1},
    {"id": 31, "name": "门铃", "parent_id": 3, "sort_order": 2},
]


@router.get("")
def list_categories(admin: dict = Depends(get_current_admin)):
    """全部分类列表。"""
    # TODO: 小D — SELECT * FROM shop.categories ORDER BY sort_order
    return success_response({"items": MOCK_CATEGORIES})


@router.post("")
def create_category(body: CreateCategoryRequest, admin: dict = Depends(get_current_admin)):
    """创建分类。"""
    # TODO: 小D — INSERT INTO shop.categories (name, parent_id) RETURNING id
    # 然后 delete_cache("categories:tree")
    return success_response({
        "id": 100,
        "name": body.name,
        "parent_id": body.parent_id,
    })


@router.put("/{category_id}")
def update_category(category_id: int, body: UpdateCategoryRequest, admin: dict = Depends(get_current_admin)):
    """编辑分类。"""
    # TODO: 小D — UPDATE shop.categories SET name=%s, parent_id=%s WHERE id=%s
    # 然后 delete_cache("categories:tree")
    return success_response({
        "id": category_id,
        "name": body.name,
        "parent_id": body.parent_id,
    })


@router.delete("/{category_id}")
def delete_category(category_id: int, admin: dict = Depends(get_current_admin)):
    """删除分类（有商品引用则拒绝）。"""
    # TODO: 小D —
    # 1. SELECT COUNT(*) FROM shop.products WHERE category_id = %s
    # 2. 有引用则 raise BusinessError("该分类下有商品，无法删除")
    # 3. DELETE FROM shop.categories WHERE id = %s
    # 4. delete_cache("categories:tree")
    return success_response({"message": "删除成功"})
