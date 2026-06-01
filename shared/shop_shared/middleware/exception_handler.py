"""全局异常处理器 — ShopException 子类自动映射为统一 JSON 响应。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..common.exceptions import ShopException
from ..common.response import error_response


def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI 应用上注册全局异常处理器。"""

    @app.exception_handler(ShopException)
    async def handle_shop_exception(request: Request, exc: ShopException):
        return JSONResponse(
            status_code=exc.http_status,
            content=error_response(code=exc.code, message=exc.message),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_response(code=50002, message="服务器内部错误"),
        )
