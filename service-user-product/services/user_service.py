"""用户业务逻辑层。

★ 小B：用户认证相关业务逻辑。

参考：shop_shared.infrastructure.database.get_cursor()
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
import jwt
from psycopg2.extras import RealDictRow

from shop_shared.infrastructure.database import get_cursor


JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-here")
JWT_ALGORITHM = "HS256"


def generate_jwt(user_id: int, email: str, role: str) -> str:
    """生成 JWT Token。"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_password(password: str) -> str:
    """使用 bcrypt 加密密码。"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确。"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_user_by_email(email: str) -> Optional[Dict]:
    """根据邮箱查询用户。"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, password, nickname, role, address FROM shop.users WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """根据用户 ID 查询用户。"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname, role, address FROM shop.users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(email: str, password: str, nickname: str) -> Dict:
    """创建新用户。"""
    hashed_password = hash_password(password)
    
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO shop.users (email, password, nickname, role, created_at)
               VALUES (%s, %s, %s, 'user', NOW())
               RETURNING id, email, nickname""",
            (email, hashed_password, nickname)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_user_address(user_id: int, address: str) -> Dict:
    """更新用户地址。"""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE shop.users SET address = %s WHERE id = %s
               RETURNING id, address""",
            (address, user_id)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def check_email_exists(email: str) -> bool:
    """检查邮箱是否已被注册。"""
    with get_cursor() as cur:
        cur.execute("SELECT id FROM shop.users WHERE email = %s", (email,))
        return cur.fetchone() is not None
