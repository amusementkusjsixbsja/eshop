"""工具定义与执行 — 供 LLM 调用的业务工具。"""

from clients.shop_client import ShopInternalClient

_client = ShopInternalClient()

# ── 工具定义（给 LLM 看的 Schema） ──

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "查询当前用户的基本信息（昵称、邮箱等）",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders",
            "description": "查询当前用户的订单列表",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_detail",
            "description": "查询某个订单的详细信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "订单 ID",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_logistics",
            "description": "查询物流进度和配送信息",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_after_sales",
            "description": "查询售后申请记录（退款/退货/换货）",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "搜索商品，根据关键词查找商品列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]

# ── 工具映射（名 → 函数） ──

TOOL_MAP = {
    "get_user_info": _client.get_user,
    "get_orders": _client.get_orders,
    "get_order_detail": _client.get_order_detail,
    "get_logistics": _client.get_logistics,
    "get_after_sales": _client.get_after_sales,
    "search_products": _client.search_products,
}


def execute_tool(name: str, arguments: dict, user_id: int) -> str:
    """执行工具并返回结果字符串（给 LLM 看的）。

    参数 user_id 由系统自动传入（从 JWT 解析），无需 LLM 提供。
    """
    func = TOOL_MAP.get(name)
    if not func:
        return f"错误：未知工具 {name}"
    try:
        arguments.setdefault("user_id", user_id)
        result = func(**arguments)
        return str(result)
    except Exception as e:
        return f"工具执行出错：{e}"
