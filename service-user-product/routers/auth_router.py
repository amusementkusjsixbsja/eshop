"""★ 小B：认证路由 — 用户注册/登录/JWT/个人信息

接口说明（对照需求文档第五章、第六章）：
  - POST /auth/register — 注册：邮箱唯一，密码 bcrypt 加密 ≥6 位
  - POST /auth/login — 登录：bcrypt 比对密码，签发 JWT (24h)
  - GET  /auth/me — 个人信息：从 JWT 获取 user_id 查询
  - PUT  /auth/address — 更新收货地址
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.common.exceptions import AuthenticationError, BusinessError
from shop_shared.middleware import get_current_user

from services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_address,
    check_email_exists,
    verify_password,
    generate_jwt,
)

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


# ─── 路由 ───

@router.post("/register")
def register(body: RegisterRequest):
    """用户注册。"""
    if check_email_exists(body.email):
        raise BusinessError("该邮箱已被注册")
    
    user = create_user(body.email, body.password, body.nickname)
    
    if not user:
        raise BusinessError("注册失败")
    
    return success_response({
        "id": user["id"],
        "email": user["email"],
        "nickname": user["nickname"],
    })


@router.post("/login")
def login(body: LoginRequest):
    """用户登录，返回 JWT Token。"""
    user = get_user_by_email(body.email)
    
    if not user:
        raise AuthenticationError("邮箱或密码错误")
    
    if not verify_password(body.password, user["password"]):
        raise AuthenticationError("邮箱或密码错误")
    
    token = generate_jwt(user["id"], user["email"], user["role"])
    
    return success_response({
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "nickname": user["nickname"],
            "role": user["role"],
        },
    })


@router.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    user_data = get_user_by_id(user["user_id"])
    
    if not user_data:
        raise AuthenticationError("用户不存在")
    
    return success_response(user_data)


@router.put("/address")
def update_address(body: AddressRequest, user: dict = Depends(get_current_user)):
    """更新收货地址。"""
    result = update_user_address(user["user_id"], body.address)
    
    if not result:
        raise AuthenticationError("用户不存在")
    
    return success_response({
        "id": result["id"],
        "address": result["address"],
    })
