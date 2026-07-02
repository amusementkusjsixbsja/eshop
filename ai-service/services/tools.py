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
            "description": "搜索商品，根据关键词和价格区间查找商品列表。当用户询问价格范围时，请使用 min_price 和 max_price 参数；如需列出全部商品，keyword 传空字符串即可",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（模糊匹配商品名称和描述，需要搜索全部商品时传空字符串）",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "最低价格（可选，筛选价格 ≥ 此值的商品，如 100）",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "最高价格（可选，筛选价格 ≤ 此值的商品，如 500）",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    # 7. create_order — 对话下单（v2.0）
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "为用户创建订单。请在多轮对话中确认商品、数量、收货地址后，经用户最终确认才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer", "description": "商品 ID"},
                                "quantity": {"type": "integer", "description": "数量"},
                            },
                            "required": ["product_id", "quantity"],
                        },
                        "description": "商品列表，每项包含商品 ID 和数量",
                    },
                    "address": {"type": "string", "description": "收货地址完整文本"},
                },
                "required": ["items", "address"],
            },
        },
    },
    # 8. pay_order — 执行支付（v2.0）
    {
        "type": "function",
        "function": {
            "name": "pay_order",
            "description": "为订单执行支付。请在用户确认支付后调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "订单 ID"},
                    "payment_method": {
                        "type": "string",
                        "enum": ["wechat", "alipay", "card", "balance"],
                        "description": "支付方式：微信/支付宝/银行卡/余额",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    # 9. get_product_reviews — 获取商品评价（v2.0）
    {
        "type": "function",
        "function": {
            "name": "get_product_reviews",
            "description": "获取某商品的用户评价和评分统计。用户询问商品口碑、质量、使用体验时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "商品 ID"},
                    "product_name": {"type": "string", "description": "商品名称（便于AI引用）"},
                },
                "required": ["product_id"],
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
    "create_order": _client.create_order,
    "pay_order": _client.pay_order,
    "get_product_reviews": _client.get_product_reviews,
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
