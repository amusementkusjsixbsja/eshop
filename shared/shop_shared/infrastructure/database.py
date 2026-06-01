"""数据库连接池 — psycopg2 ThreadedConnectionPool。"""

import os
import threading
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2 import pool as pg_pool, extras

from ..common.exceptions import DatabaseError
from ..common.logger import get_logger

logger = get_logger("database")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:1234@postgres:5432/agent")

_pool: Optional[pg_pool.ThreadedConnectionPool] = None
_pool_lock = threading.Lock()


def init_pool(minconn: int = 2, maxconn: int = 10) -> None:
    """初始化全局连接池。在 lifespan 启动时调用。"""
    global _pool
    with _pool_lock:
        if _pool is not None:
            logger.warning("连接池已存在，跳过初始化")
            return
        try:
            _pool = pg_pool.ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dsn=DATABASE_URL,
            )
            # 设置所有连接的 search_path
            conn = _pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO shop")
                conn.commit()
            finally:
                _pool.putconn(conn)
            logger.info("数据库连接池已初始化 (min=%d, max=%d)", minconn, maxconn)
        except Exception as e:
            logger.error("数据库连接池初始化失败: %s", e)
            raise DatabaseError(f"数据库连接失败: {e}")


def close_pool() -> None:
    """关闭连接池。在 lifespan 关闭时调用。"""
    global _pool
    with _pool_lock:
        if _pool:
            _pool.closeall()
            _pool = None
            logger.info("数据库连接池已关闭")


def get_connection():
    """从池中获取一个连接。"""
    if _pool is None:
        raise DatabaseError("数据库连接池未初始化")
    try:
        return _pool.getconn()
    except Exception as e:
        logger.error("获取数据库连接失败: %s", e)
        raise DatabaseError(f"获取数据库连接失败: {e}")


def release_connection(conn) -> None:
    """归还连接到池。"""
    if _pool and conn:
        _pool.putconn(conn)


@contextmanager
def get_cursor(commit: bool = True):
    """自动事务管理的游标上下文管理器。

    with get_cursor() as cur:
        cur.execute("SELECT ...")
        row = cur.fetchone()

    退出时自动 COMMIT（成功）或 ROLLBACK（异常），自动归还连接。
    适用于单条 SQL 或简单的原子操作。
    复杂事务（下单/支付/取消）请使用手动事务模式。
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)
