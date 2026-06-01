"""Redis 客户端 — Cache-Aside 模式封装。"""

import json
import os
from typing import Any, List, Optional

import redis

from ..common.logger import get_logger

logger = get_logger("redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_redis_client: Optional[redis.Redis] = None


def init_redis() -> None:
    """初始化 Redis 客户端。在 lifespan 启动时调用。"""
    global _redis_client
    try:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis 客户端已连接")
    except Exception as e:
        logger.warning("Redis 连接失败，缓存将降级为直接查 DB: %s", e)
        _redis_client = None


def close_redis() -> None:
    """关闭 Redis 连接。在 lifespan 关闭时调用。"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None
        logger.info("Redis 连接已关闭")


def get_redis() -> Optional[redis.Redis]:
    return _redis_client


# ——— 缓存操作封装 ———

def get_cache(key: str) -> Any:
    """读取缓存 JSON → 反序列化返回。失败/不存在返回 None。"""
    client = _redis_client
    if client is None:
        return None
    try:
        data = client.get(key)
        return json.loads(data) if data else None
    except Exception:
        logger.warning("Redis 读取失败 (key=%s)，降级查 DB", key)
        return None


def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """序列化 JSON → 写入 Redis，带 TTL。"""
    client = _redis_client
    if client is None:
        return
    try:
        client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        logger.warning("Redis 写入失败 (key=%s)", key)


def delete_cache(key: str) -> None:
    """删除单个缓存 key。"""
    client = _redis_client
    if client is None:
        return
    try:
        client.delete(key)
    except Exception:
        logger.warning("Redis 删除失败 (key=%s)", key)


def delete_keys(keys: List[str]) -> None:
    """批量删除缓存 key（使用 Redis Pipeline）。"""
    client = _redis_client
    if client is None:
        return
    try:
        pipeline = client.pipeline()
        for key in keys:
            pipeline.delete(key)
        pipeline.execute()
    except Exception:
        logger.warning("Redis 批量删除失败 (keys=%s)", keys)
