"""RequestLogMiddleware — 记录每个请求的方法、路径、状态码、耗时。"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..common.logger import get_logger

logger = get_logger("middleware")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """拦截请求 → 记录耗时 → 输出日志到 stdout。"""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000  # 毫秒

        logger.info(
            "%s %s → %d | %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response
