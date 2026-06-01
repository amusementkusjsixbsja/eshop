"""JWT 解码工具 — 供 AI 服务提取用户身份。

AI 服务与 shop-service 共享 JWT_SECRET。
参考: shop_shared.middleware.auth
"""

import os

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")


def extract_user_from_token(authorization: str | None) -> dict:
    """从 Authorization Header 解码用户 JWT。

    返回: {"user_id": int, "email": str, "role": str}

    安全规则：
      - user_id 必须从 JWT 中解码获得，绝对不可由前端传入
      - 防止用户篡改参数查看他人数据
    """
    if not authorization:
        raise ValueError("缺失 Authorization Header，请先登录")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Authorization 格式错误，应为 Bearer <token>")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise ValueError("Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise ValueError("Token 无效，请重新登录")
    except (ValueError, IndexError):
        raise ValueError("Authorization 格式错误")
