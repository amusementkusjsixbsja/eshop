"""★ 小B：认证路由 — 用户注册/登录/JWT/个人信息

接口说明（对照需求文档第五章、第六章）：
  - POST /auth/register — 注册：邮箱唯一，密码 bcrypt 加密 ≥6 位
  - POST /auth/login — 登录：bcrypt 比对密码，签发 JWT (24h)
  - GET  /auth/me — 个人信息：从 JWT 获取 user_id 查询
  - PUT  /auth/address — 更新收货地址
"""

import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from shop_shared.common import success_response
from shop_shared.common.exceptions import AuthenticationError, BusinessError
from shop_shared.infrastructure.database import get_cursor
from shop_shared.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def generate_jwt(user_id: int, email: str, role: str) -> str:
    """生成 JWT Token。"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_password(password: str) -> str:
    """使用 bcrypt 加密密码。"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


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
    # 1. 校验邮箱唯一性
    with get_cursor() as cur:
        cur.execute("SELECT id FROM shop.users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise BusinessError("该邮箱已被注册")
        
        # 2. bcrypt 加密密码
        hashed_password = hash_password(body.password)
        
        # 3. 插入用户数据
        cur.execute(
            "INSERT INTO shop.users (email, password, nickname, created_at, updated_at) "
            "VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id",
            (body.email, hashed_password, body.nickname)
        )
        user = cur.fetchone()
    
    return success_response({
        "id": user["id"],
        "email": body.email,
        "nickname": body.nickname,
    })


@router.post("/login")
def login(body: LoginRequest):
    """用户登录，返回 JWT Token。"""
    # 1. 根据邮箱查询用户
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, password, nickname, role FROM shop.users WHERE email = %s",
            (body.email,)
        )
        user = cur.fetchone()
    
    # 2. 校验用户存在
    if not user:
        raise AuthenticationError("邮箱或密码错误")
    
    # 3. bcrypt 比对密码
    if not bcrypt.checkpw(body.password.encode(), user["password"].encode()):
        raise AuthenticationError("邮箱或密码错误")
    
    # 4. 生成 JWT Token
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
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname, role, address FROM shop.users WHERE id = %s",
            (user["user_id"],)
        )
        user_data = cur.fetchone()
    
    if not user_data:
        raise AuthenticationError("用户不存在")
    
    return success_response({
        "id": user_data["id"],
        "email": user_data["email"],
        "nickname": user_data["nickname"],
        "role": user_data["role"],
        "address": user_data["address"],
    })


@router.put("/address")
def update_address(body: AddressRequest, user: dict = Depends(get_current_user)):
    """更新收货地址。"""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE shop.users SET address = %s, updated_at = NOW() WHERE id = %s RETURNING id, address",
            (body.address, user["user_id"])
        )
        result = cur.fetchone()
    
    if not result:
        raise AuthenticationError("用户不存在")
    
    return success_response({
        "id": result["id"],
        "address": result["address"],
    })
