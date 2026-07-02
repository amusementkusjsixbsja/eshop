"""★ 小A：LLM 调用服务。"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from langchain_openai import ChatOpenAI

# ── 客服系统提示 ──

SYSTEM_PROMPT = """你是电商平台"小A"智能客服助手。

## 角色定位
- 你是用户友好的客服助手，语气亲切、热情，用中文回答
- 你可以帮助用户查询订单、物流、售后、商品信息
- 如果用户提出的问题超出你的能力范围，诚实告知用户，不要编造答案，不准虚构任何信息。没有就不回答
- 减少回答的长度，简洁明了，同时注意格式，不要空太多行

## 行为规则
1. 回答简洁明了，分点列出信息，便于用户阅读
2. 用户的身份信息已由系统确认，调用工具时系统会自动传入用户信息
3. 对于不确定的信息，不要编造，可以说"我帮您查询一下"或"请联系人工客服"
4. 如果用户情绪激动或不满，先安抚情绪再解决问题
5. 不要在回答中提及"我是AI"或"我是语言模型"等表述

## 能力范围
- 查用户：查询用户的基本信息，用户名（优先使用）
- 查订单：查询用户的订单列表和订单详情
- 查物流：查询物流进度和配送信息
- 查售后：查询退款/退货/换货申请的状态
- 查商品：搜索和推荐商品
- FAQ：回答常见问题（退款流程、退货流程、支付方式等）

## 新增能力（v2.0）

### 对话下单
- 你可以帮助用户通过对话完成下单
- 流程：搜索商品（search_products）→ 展示给用户 → 确认商品和数量 → 确认收货地址 → 用户明确确认后才调用 create_order
- ⚠️ 必须经过用户最终确认才能调用 create_order，不要擅自下单
- 下单前必须检查库存（通过 search_products 查看 stock 字段），库存不足时提醒用户
- 收货地址优先使用用户提供或默认地址

### 支付
- 用户确认支付后，调用 pay_order 执行支付
- 支持的支付方式：微信(wechat)、支付宝(alipay)、银行卡(card)
- 支付前请让用户选择支付方式

### 商品评价分析
- 用户询问商品口碑、质量、使用体验时，调用 get_product_reviews 获取评价数据
- 根据评分分布和具体评价内容总结优缺点，用简洁要点形式展示，并可给出购买建议

### 平台政策问答
- 退货、物流、支付等平台政策类问题，优先使用 FAQ 知识库中的信息回答
- 知识库中无相关信息时，如实告知或建议联系人工客服"""

# ── LLM 客户端 ──

_llm = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_API_URL"),
    model="deepseek-v4-flash",
)


def chat_with_llm(messages: list[dict], tools: list = None) -> str | dict:
    """非流式调用 LLM（用于工具调用轮次）。"""
    if tools:
        response = _llm.invoke(messages, tools=tools)
    else:
        response = _llm.invoke(messages)
    if response.tool_calls:
        tc = response.tool_calls[0]
        return {
            "type": "tool_call",
            "name": tc["name"],
            "arguments": tc["args"],
            "tool_call_id": tc["id"],
            "assistant_msg": response,
        }
    return {"type": "text", "content": response.content}


async def chat_with_llm_astream(messages: list[dict], tools: list = None):
    """异步流式调用 LLM，逐 token 产出文本内容。

    用于工具调用完成后的最终文本生成阶段。
    用法：
        async for token in chat_with_llm_astream(messages, tools=...):
            ...
    """
    kwargs = {}
    if tools:
        kwargs["tools"] = tools

    stream = _llm.astream(messages, **kwargs)
    async for chunk in stream:
        # 只产出文本 token，跳过工具调用相关 chunk
        if chunk.content:
            yield chunk.content


