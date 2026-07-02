"""地址管理路由 — 多地址 CRUD + 默认地址设置。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.common.exceptions import NotFoundError, BusinessError
from shop_shared.middleware import get_current_user
from shop_shared.infrastructure.database import get_cursor

router = APIRouter(prefix="/addresses", tags=["地址管理"])


# ─── Pydantic 模型 ───

class AddressCreate(BaseModel):
    label: str = ''
    name: str
    phone: str
    address: str
    is_default: bool = False

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: str) -> str:
        if not v or len(v) < 7:
            raise ValueError("请输入有效的手机号")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("请输入收货人姓名")
        return v.strip()

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("请输入收货地址")
        return v.strip()


class AddressUpdate(BaseModel):
    label: str | None = None
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    is_default: bool | None = None


# ─── 路由 ───

@router.get("")
def list_addresses(user: dict = Depends(get_current_user)):
    """获取当前用户的所有地址。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, user_id, label, name, phone, address, is_default, created_at
            FROM shop.user_addresses
            WHERE user_id = %s
            ORDER BY is_default DESC, created_at DESC
        """, (user["user_id"],))
        rows = cur.fetchall()
    return success_response({"items": [dict(r) for r in rows]})


@router.post("")
def create_address(body: AddressCreate, user: dict = Depends(get_current_user)):
    """创建新地址。"""
    user_id = user["user_id"]
    with get_cursor() as cur:
        # 如果是第一个地址或标记为默认，清除其他默认
        if body.is_default:
            cur.execute("UPDATE shop.user_addresses SET is_default = FALSE WHERE user_id = %s", (user_id,))
        cur.execute("""
            INSERT INTO shop.user_addresses (user_id, label, name, phone, address, is_default)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, body.label, body.name, body.phone, body.address, body.is_default))
        addr_id = cur.fetchone()["id"]
    return success_response({"id": addr_id})


@router.put("/{address_id}")
def update_address(address_id: int, body: AddressUpdate, user: dict = Depends(get_current_user)):
    """更新地址。"""
    user_id = user["user_id"]
    with get_cursor() as cur:
        cur.execute("SELECT id FROM shop.user_addresses WHERE id = %s AND user_id = %s", (address_id, user_id))
        if not cur.fetchone():
            raise NotFoundError("地址不存在")

        if body.is_default:
            cur.execute("UPDATE shop.user_addresses SET is_default = FALSE WHERE user_id = %s", (user_id,))

        updates = []
        params = []
        for field in ["label", "name", "phone", "address", "is_default"]:
            val = getattr(body, field, None)
            if val is not None:
                updates.append(f"{field} = %s")
                params.append(val)
        if not updates:
            raise BusinessError("没有需要更新的字段")
        updates.append("updated_at = NOW()")
        params.extend([address_id, user_id])
        cur.execute(f"""
            UPDATE shop.user_addresses SET {', '.join(updates)}
            WHERE id = %s AND user_id = %s
        """, params)
    return success_response({"id": address_id})


@router.delete("/{address_id}")
def delete_address(address_id: int, user: dict = Depends(get_current_user)):
    """删除地址。"""
    with get_cursor() as cur:
        cur.execute("DELETE FROM shop.user_addresses WHERE id = %s AND user_id = %s RETURNING id",
                    (address_id, user["user_id"]))
        if not cur.fetchone():
            raise NotFoundError("地址不存在")
    return success_response({"message": "地址已删除"})


@router.patch("/{address_id}/default")
def set_default_address(address_id: int, user: dict = Depends(get_current_user)):
    """设为默认地址。"""
    user_id = user["user_id"]
    with get_cursor() as cur:
        cur.execute("SELECT id FROM shop.user_addresses WHERE id = %s AND user_id = %s", (address_id, user_id))
        if not cur.fetchone():
            raise NotFoundError("地址不存在")
        cur.execute("UPDATE shop.user_addresses SET is_default = FALSE WHERE user_id = %s", (user_id,))
        cur.execute("UPDATE shop.user_addresses SET is_default = TRUE WHERE id = %s", (address_id,))
    return success_response({"id": address_id, "is_default": True})
