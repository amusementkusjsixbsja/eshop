"""★ 小A：ai-service 数据库连接池。

供 FAQ 向量检索和对话持久化使用，连接 customer_service schema 所在的 PostgreSQL。

原 ai-service 不直接连数据库，本模块为第二轮新增。采用懒加载单连接 +
autocommit 的简单实现（并发量小，够用）。
"""

import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:1234@postgres:5432/agent")

# 懒加载单连接（生产环境可替换为 psycopg2.pool.ThreadedConnectionPool）
_conn = None


def get_connection():
    """获取数据库连接（懒加载，断线自动重连）。"""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(DATABASE_URL)
        _conn.autocommit = True
    return _conn


@contextmanager
def get_cursor():
    """获取数据库游标（上下文管理器，返回 RealDictCursor）。"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()


def close_connection():
    """关闭数据库连接。"""
    global _conn
    if _conn and not _conn.closed:
        _conn.close()
    _conn = None
