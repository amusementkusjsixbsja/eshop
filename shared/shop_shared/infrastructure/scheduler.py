"""APScheduler 调度器 — 进程内 BackgroundScheduler。"""

import os
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from ..common.logger import get_logger

logger = get_logger("scheduler")

_scheduler: Optional[BackgroundScheduler] = None


def init_scheduler() -> BackgroundScheduler:
    """创建并启动调度器。在 lifespan 启动时调用。"""
    global _scheduler
    _scheduler = BackgroundScheduler(
        timezone="Asia/Shanghai",
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        },
    )
    _scheduler.start()
    logger.info("APScheduler 调度器已启动")
    return _scheduler


def shutdown_scheduler() -> None:
    """关闭调度器。在 lifespan 关闭时调用。"""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler 调度器已关闭")


def get_scheduler() -> Optional[BackgroundScheduler]:
    return _scheduler
