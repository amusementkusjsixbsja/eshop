"""RequestIDMiddleware — 每个请求分配唯一 ID，贯穿所有日志。"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..common.context import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """从 Header 读取或生成 request_id → 存入 ContextVar → 回写响应头。"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
