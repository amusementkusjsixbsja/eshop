"""Logger 配置 — 仅输出 stdout，Docker 日志驱动收集。"""

import logging
import sys

from .context import request_id_var


class RequestIDFilter(logging.Filter):
    """从 ContextVar 注入 request_id 到每条日志记录。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def setup_logger(level: str = "INFO") -> None:
    """配置根 Logger：格式化输出到 stdout。

    应在 FastAPI lifespan 启动时调用一次。
    """
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(request_id)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    # 清除已有 handler（防止重复添加）
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # 抑制第三方库的 DEBUG 日志
    for lib in ["apscheduler", "redis"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取带模块名的 Logger。"""
    return logging.getLogger(name)
