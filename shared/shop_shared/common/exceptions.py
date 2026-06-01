"""统一异常树 — 所有业务异常继承自 ShopException，自动映射为统一 JSON 响应。"""


class ShopException(Exception):
    """业务异常基类"""

    code: int = 50000
    http_status: int = 500
    message: str = "服务器内部错误"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)


class ValidationError(ShopException):
    """参数校验失败 (400)"""
    code = 40001
    http_status = 400
    message = "参数校验失败"


class AuthenticationError(ShopException):
    """未登录或 Token 过期 (401)"""
    code = 40101
    http_status = 401
    message = "未登录或 Token 过期"


class PermissionDeniedError(ShopException):
    """无操作权限 (403)"""
    code = 40301
    http_status = 403
    message = "无操作权限"


class NotFoundError(ShopException):
    """资源不存在 (404)"""
    code = 40401
    http_status = 404
    message = "资源不存在"


class BusinessError(ShopException):
    """业务规则冲突 — 库存不足、状态不允许等 (422)"""
    code = 42201
    http_status = 422
    message = "业务规则冲突"


class DatabaseError(ShopException):
    """数据库异常 (500)"""
    code = 50001
    http_status = 500
    message = "数据库异常"


class InternalError(ShopException):
    """未预期的内部错误 (500)"""
    code = 50002
    http_status = 500
    message = "服务器内部错误"
