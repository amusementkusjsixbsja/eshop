"""★ 小B：认证路由 — 将此文件的 mock 数据替换为真实数据库查询。

接口说明（对照需求文档第五章、第六章）：
  - POST /auth/register — 注册：邮箱唯一，密码 bcrypt 加密 ≥6 位
  - POST /auth/login — 登录：bcrypt 比对密码，签发 JWT (24h)
  - GET  /auth/me — 个人信息：从 JWT 获取 user_id 查询
  - PUT  /auth/address — 更新收货地址
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


# ─── Pydantic 请求模型 ───

class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度不能少于 6 位")
        return v

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("请输入有效的邮箱地址")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class AddressRequest(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("收货地址不能为空")
        return v.strip()


# ─── 路由（Stub 版本，返回 mock 数据）───

@router.post("/register")
def register(body: RegisterRequest):
    """用户注册。"""
    # TODO: 小B — 替换为真实注册逻辑
    # 1. 校验邮箱唯一性 (SELECT email FROM shop.users WHERE email = %s)
    # 2. bcrypt 加密密码 (bcrypt.hashpw(password.encode(), bcrypt.gensalt()))
    # 3. INSERT INTO shop.users (email, password, nickname) RETURNING id
    # 4. 返回成功
    return success_response({
        "id": 1,
        "email": body.email,
        "nickname": body.nickname,
    })


@router.post("/login")
def login(body: LoginRequest):
    """用户登录，返回 JWT Token。"""
    # TODO: 小B — 替换为真实登录逻辑
    # 1. SELECT * FROM shop.users WHERE email = %s → 查不到则 raise AuthenticationError
    # 2. bcrypt.checkpw(password.encode(), row["password"].encode()) → 不匹配则 raise
    # 3. jwt.encode({user_id, email, role, exp}, JWT_SECRET, algorithm="HS256")
    # 4. 返回 token + user 信息
    return success_response({
        "token": "mock-jwt-token-please-replace",
        "user": {
            "id": 1,
            "email": body.email,
            "nickname": "测试用户",
            "role": "user",
        },
    })


@router.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    # TODO: 小B — 替换为真实查询
    # SELECT id, email, nickname, role, address FROM shop.users WHERE id = %s
    return success_response({
        "id": user["user_id"],
        "email": user["email"],
        "nickname": "测试用户",
        "role": user["role"],
        "address": "广东省深圳市南山区",
    })


@router.put("/address")
def update_address(body: AddressRequest, user: dict = Depends(get_current_user)):
    """更新收货地址。"""
    # TODO: 小B — 替换为真实更新逻辑
    # UPDATE shop.users SET address = %s, updated_at = NOW() WHERE id = %s
    return success_response({
        "id": user["user_id"],
        "address": body.address,
    })
