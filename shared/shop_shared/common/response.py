"""统一响应格式工具函数。"""

from typing import Any

from .context import request_id_var


def success_response(data: Any = None, message: str = "success") -> dict:
    """成功响应: {"code": 0, "data": ..., "message": "success"}"""
    return {"code": 0, "data": data, "message": message}


def error_response(code: int, message: str, data: Any = None) -> dict:
    """错误响应: {"code": N, "data": ..., "message": "...", "request_id": "..."}"""
    resp = {"code": code, "data": data, "message": message}
    request_id = request_id_var.get("-")
    if request_id != "-":
        resp["request_id"] = request_id
    return resp


def paginated_response(items: list, total: int, page: int, size: int) -> dict:
    """分页列表响应。"""
    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    })
