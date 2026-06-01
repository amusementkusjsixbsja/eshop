"""★ 小A：AI 对话路由。

接口说明（对照 AI服务对接开发指南）：
  - POST /api/ai/chat — 用户发送消息，AI 回复

认证方式：
  - Authorization: Bearer <user_jwt>（AI 服务解码 JWT 得到 user_id）
  - ★ 关键安全规则：user_id 必须从 JWT 解码获取，不可由前端传入

工作流程：
  1. 解码 JWT，提取 user_id
  2. 意图识别（FAQ / 查订单 / 查物流 / 查售后 / 查商品）
  3. FAQ 类：检索 pgvector FAQ 知识库
  4. 实时数据类：调用 shop-service 内部接口（ShopInternalClient）
  5. LLM 生成自然语言回复
  6. 返回 {answer, data?}
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel

from shop_shared.common import success_response
from shop_shared.common.logger import get_logger

from utils.auth import extract_user_from_token
from clients.shop_client import ShopInternalClient

logger = get_logger("chat")
shop_client = ShopInternalClient()

router = APIRouter(tags=["AI 客服"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    data: dict | None = None


@router.post("/chat")
def chat(
    body: ChatRequest,
    authorization: str = Header(None),
):
    """AI 对话接口。"""
    # 1. 解码 JWT 获取用户身份
    try:
        user = extract_user_from_token(authorization)
        user_id = user["user_id"]
    except Exception as e:
        return ChatResponse(answer=str(e))

    question = body.question.strip()

    # 2. 意图识别（目前为关键词匹配，可替换为 LLM 分类）
    # ★ 小A：可以替换为更智能的意图分类
    intent = _detect_intent(question)
    logger.info("意图识别结果: intent=%s, question=%s", intent, question)

    # 3. 根据意图处理
    if intent == "faq":
        answer = _handle_faq(question)
        return ChatResponse(answer=answer)

    elif intent == "order":
        data = shop_client.get_orders(user_id=user_id)
        answer = _format_order_response(data)
        return ChatResponse(answer=answer, data=data.get("data"))

    elif intent == "logistics":
        data = shop_client.get_logistics(user_id=user_id)
        answer = _format_logistics_response(data)
        return ChatResponse(answer=answer, data=data.get("data"))

    elif intent == "after_sale":
        data = shop_client.get_after_sales(user_id=user_id)
        answer = _format_after_sale_response(data)
        return ChatResponse(answer=answer, data=data.get("data"))

    elif intent == "product":
        # 从问题中提取关键词
        keyword = question.replace("推荐", "").replace("有什么", "").replace("商品", "").strip()
        data = shop_client.search_products(keyword=keyword or "热门", size=5)
        answer = _format_product_response(data, keyword)
        return ChatResponse(answer=answer, data=data.get("data"))

    else:
        # 意图不明确 → 反问澄清
        answer = "请问您想了解什么？我可以帮您：\n1. 查询订单信息\n2. 查询物流进度\n3. 查看商品推荐\n4. 了解常见问题（如退款流程）"
        return ChatResponse(answer=answer)


# ─── 内部处理函数 ───

def _detect_intent(question: str) -> str:
    """简单的关键词意图识别。

    ★ 小A：此函数可替换为 LLM 意图分类。
    """
    q = question.lower()

    # 订单相关
    if any(kw in q for kw in ["订单", "买了", "购物", "下单", "购买记录"]):
        return "order"

    # 物流相关
    if any(kw in q for kw in ["物流", "快递", "到哪", "配送", "运单", "发货", "运输"]):
        return "logistics"

    # 售后相关
    if any(kw in q for kw in ["售后", "退货", "退款", "换货", "维修"]):
        return "after_sale"

    # 商品相关
    if any(kw in q for kw in ["推荐", "有什么", "商品", "产品", "热门", "新款"]):
        return "product"

    # FAQ 类
    if any(kw in q for kw in ["怎么", "如何", "什么", "吗", "？", "客服", "帮助", "说明"]):
        return "faq"

    return "unknown"


def _handle_faq(question: str) -> str:
    """FAQ 知识库检索。

    ★ 小A：替换为 pgvector 向量检索 或 LLM 生成回答。
    当前为关键词匹配的 mock 版本。
    """
    q = question.lower()

    faq = {
        "退款": "退款流程：\n1. 在订单详情页点击「申请售后」\n2. 选择「退款」类型并填写原因\n3. 提交后等待管理员审核\n4. 审核通过后款项将原路返回",
        "退货": "退货流程：\n1. 在订单详情页点击「申请售后」\n2. 选择「退货」类型并填写原因\n3. 审核通过后将收到退货地址\n4. 寄回商品后确认完成",
        "密码": "修改密码请进入个人中心 → 安全设置 → 修改密码（此功能开发中，暂不可用）",
        "支付": "本平台支持模拟支付。在订单详情页点击「支付」按钮即可完成支付。",
        "物流": "物流信息请在订单详情页点击「查看物流」查询。",
    }

    for keyword, answer in faq.items():
        if keyword in q:
            return answer

    return "感谢您的咨询！您可以在「我的订单」中查看订单信息，或在商品页面浏览更多商品。如需进一步帮助，请联系人工客服。"


def _format_order_response(data: dict) -> str:
    """格式化订单数据为自然语言。"""
    items = data.get("data", {}).get("items", [])
    if not items:
        return "您目前没有订单记录。"
    lines = ["您有以下订单："]
    for o in items:
        status_map = {"pending": "待支付", "paid": "已支付", "cancelled": "已取消"}
        status_cn = status_map.get(o.get("status", ""), o.get("status", ""))
        lines.append(f"- 订单 #{o['id']}：{o.get('total_amount', 0)}元，状态：{status_cn}")
    return "\n".join(lines)


def _format_logistics_response(data: dict) -> str:
    """格式化物流数据为自然语言。"""
    items = data.get("data", {}).get("items", [])
    if not items:
        return "暂时没有物流信息。"
    log = items[0]
    status_map = {"picked_up": "已揽件", "in_transit": "运输中", "out_for_delivery": "派送中", "delivered": "已签收"}
    status_cn = status_map.get(log.get("status", ""), log.get("status", ""))
    location = log.get("current_location", "未知")
    timeline = log.get("timeline", [])
    lines = [
        f"物流状态：{status_cn}",
        f"当前位置：{location}",
        f"承运方：{log.get('carrier', '')}  运单号：{log.get('tracking_number', '')}",
    ]
    if timeline:
        lines.append("\n运输节点：")
        for t in timeline:
            lines.append(f"  {t.get('time', '')} - {t.get('status', '')} @ {t.get('location', '')}")
    return "\n".join(lines)


def _format_after_sale_response(data: dict) -> str:
    """格式化售后数据为自然语言。"""
    items = data.get("data", {}).get("items", [])
    if not items:
        return "您没有售后申请记录。"
    lines = ["您的售后申请："]
    for a in items:
        type_map = {"refund": "退款", "return": "退货"}
        status_map = {"pending": "待处理", "approved": "已通过", "rejected": "已拒绝", "completed": "已完成"}
        lines.append(f"- #{a['id']} 订单 #{a['order_id']}：{type_map.get(a['type'], a['type'])}，状态：{status_map.get(a['status'], a['status'])}")
    return "\n".join(lines)


def _format_product_response(data: dict, keyword: str) -> str:
    """格式化商品数据为自然语言。"""
    items = data.get("data", {}).get("items", [])
    if not items:
        return f"抱歉，没有找到与「{keyword}」相关的商品。"
    lines = [f"为您找到以下商品："]
    for p in items:
        lines.append(f"- {p.get('name', '')}：¥{p.get('price', 0)}（库存{p.get('stock', 0)}件）")
    return "\n".join(lines)
