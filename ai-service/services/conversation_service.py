"""★ 小A：对话持久化服务（数据库版）。

第二轮从内存 dict 迁移到 customer_service.conversations / messages 表。
服务重启后历史仍在（旧内存实现的重启丢失问题一并解决）。
"""

import json
import uuid
from datetime import datetime

from services.database import get_cursor


def create_conversation(user_id) -> str:
    """创建新对话，返回 UUID。

    conversations.user_id 列为 TEXT，caller 可能传 int，这里统一转字符串。
    """
    conv_id = str(uuid.uuid4())
    title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO customer_service.conversations (id, user_id, title)
            VALUES (%s, %s, %s)
            """,
            (conv_id, str(user_id), title),
        )
    return conv_id


def add_message(conv_id: str, role: str, content: str, turn_number: int = None, metadata: dict = None):
    """添加一条消息到对话。

    role: 'user' / 'assistant' / 'system'
    turn_number 为空时自动取 MAX(turn_number)+1。
    """
    if turn_number is None:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(turn_number), 0) + 1 AS next_turn
                FROM customer_service.messages
                WHERE conversation_id = %s
                """,
                (conv_id,),
            )
            turn_number = cur.fetchone()["next_turn"]

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO customer_service.messages
                (conversation_id, role, content, turn_number, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (conv_id, role, content, turn_number, json.dumps(metadata) if metadata else None),
        )
        cur.execute(
            """
            UPDATE customer_service.conversations
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (conv_id,),
        )


def get_history(conv_id: str) -> list[dict]:
    """获取对话历史（按 turn_number 升序）。

    只返回 {role, content}，直接可作为 LLM messages 使用，
    不携带 turn_number/metadata 等字段以免污染 LLM 输入。
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT role, content
            FROM customer_service.messages
            WHERE conversation_id = %s
            ORDER BY turn_number ASC
            """,
            (conv_id,),
        )
        return [{"role": row["role"], "content": row["content"]} for row in cur.fetchall()]


def update_conversation_title(conv_id: str, title: str):
    """更新对话标题。"""
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE customer_service.conversations
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (title, conv_id),
        )
