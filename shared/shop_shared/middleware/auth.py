"""JWT 认证与鉴权依赖注入。

所有服务共享同一 JWT_SECRET 和 INTERNAL_API_TOKEN。
"""

import os

import jwt
from fastapi import Header, Depends

from ..common.exceptions import AuthenticationError, PermissionDeniedError

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")
JWT_ALGORITHM = "HS256"


def get_current_user(authorization: str = Header(None)) -> dict:
    """从 Authorization: Bearer <token> 解码 JWT，返回用户信息。

    用于 C 端接口的 Depends。
    返回: {"user_id": int, "email": str, "role": str}
    """
    if not authorization:
        raise AuthenticationError("未登录或 Token 过期")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise AuthenticationError("Authorization 格式错误")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Token 无效")
    except (ValueError, IndexError):
        raise AuthenticationError("Authorization 格式错误")


def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:  # noqa: F821
    """验证当前用户是否拥有管理员角色。

    用于 B 端接口的 Depends。
    """
    if current_user.get("role") != "admin":
        raise PermissionDeniedError("需要管理员权限")
    return current_user


def verify_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")) -> bool:
    """校验内部接口 Token。

    用于 /internal/* 接口的 Depends。
    """
    if x_internal_token != INTERNAL_API_TOKEN:
        raise AuthenticationError("无效的内部接口 Token")
    return True


# FastAPI Depends 已在文件顶部导入
