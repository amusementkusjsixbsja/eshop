"""★ 小A：AI 对话路由。

接口说明（对照 AI服务对接开发指南）：
  - POST /api/ai/chat — 用户发送消息，AI 回复
  - POST /api/ai/chat/stream — 流式 SSE 推送（工具调用完成后逐 token 输出）

认证方式：
  - Authorization: Bearer <user_jwt>（AI 服务解码 JWT 得到 user_id）
  - ★ 关键安全规则：user_id 必须从 JWT 解码获取，不可由前端传入
"""

import json

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shop_shared.common import success_response
from shop_shared.common.logger import get_logger

from utils.auth import extract_user_from_token
from clients.shop_client import ShopInternalClient
from services.faq_service import search_faq

logger = get_logger("chat")
shop_client = ShopInternalClient()

router = APIRouter(tags=["AI 客服"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    data: dict | None = None


# ── 工具函数：获取用户上下文 ──

def _get_user_context(authorization: str | None) -> dict:
    """从 Authorization Header 解码 JWT 并获取用户上下文。

    返回: {"user_id": int, "email": str, "role": str, "nickname": str}
    """
    try:
        payload = extract_user_from_token(authorization)
        # 补充用户昵称（从 shop 服务查询）
        try:
            user_info = shop_client.get_user(payload["user_id"])
            if user_info.get("code") == 0:
                payload["nickname"] = user_info["data"].get("nickname", "用户")
        except Exception:
            payload["nickname"] = "用户"
        return payload
    except ValueError:
        return None


# ── 工具函数：工具调用轮次（同步，非流式） ──

def _resolve_tool_calls(messages: list[dict], user_id: int = 1) -> str:
    """执行多轮工具调用，返回最终 LLM 文本回复。"""
    from services.llm_service import chat_with_llm
    from services.tools import TOOL_DEFINITIONS, execute_tool

    for _ in range(5):
        result = chat_with_llm(messages, tools=TOOL_DEFINITIONS)
        if result["type"] == "text":
            return result["content"]

        tool_result = execute_tool(result["name"], result["arguments"], user_id=user_id)
        messages.append(result["assistant_msg"])
        messages.append({
            "role": "tool",
            "tool_call_id": result["tool_call_id"],
            "content": str(tool_result),
        })

    return "抱歉，我暂时无法处理您的请求，请稍后再试。"


# ── SSE 流式生成器 ──

async def _event_stream(messages: list[dict], conv_id: str, question: str):
    """SSE 流式生成器"""
    from services.conversation_service import add_message
    from services.llm_service import chat_with_llm_astream

    yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id})}\n\n"

    full_text = ""
    try:
        async for token in chat_with_llm_astream(messages):
            if token:
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
    except Exception as e:
        full_text += "\n\n[服务异常，请重试]"
        yield f"data: {json.dumps({'type': 'error', 'content': '服务暂时不可用'})}\n\n"

    add_message(conv_id, "user", question)
    add_message(conv_id, "assistant", full_text)
    yield "data: [DONE]\n\n"


async def _event_stream_faq(answer: str, conv_id: str):
    """FAQ 命中的流式输出（直接返回完整答案，不经过 LLM）。"""
    yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id})}\n\n"
    yield f"data: {json.dumps({'type': 'token', 'content': answer})}\n\n"
    yield "data: [DONE]\n\n"


# ── 工具函数：构建带用户上下文的消息 ──

def _build_messages(question: str, conv_id: str, user_ctx: dict) -> list[dict]:
    """构建 LLM 消息列表，注入用户身份信息。"""
    from services.conversation_service import get_history
    from services.llm_service import SYSTEM_PROMPT

    # 注入用户身份到系统提示
    user_tag = f"\n\n## 当前用户\n- 用户ID: {user_ctx['user_id']}\n- 昵称: {user_ctx.get('nickname', '用户')}\n- 邮箱: {user_ctx['email']}\n- 角色: {user_ctx['role']}"
    enhanced_prompt = SYSTEM_PROMPT + user_tag

    history = get_history(conv_id)
    messages = [
        {"role": "system", "content": enhanced_prompt},
        *history,
        {"role": "user", "content": question},
    ]
    return messages


# ── 端点1：非流式 ──

@router.post("/chat")
def chat(body: ChatRequest, authorization: str = Header(None)):
    # 1) 从 JWT 提取用户身份
    user_ctx = _get_user_context(authorization)
    if not user_ctx:
        return ChatResponse(answer="请先登录后再使用AI客服。", conversation_id=None)
    user_id = user_ctx["user_id"]

    from services.conversation_service import create_conversation, add_message
    conv_id = body.conversation_id or create_conversation(user_id)

    # FAQ 优先检索：命中（相似度≥阈值）则直接返回，跳过 LLM
    faq_answer = search_faq(body.question)
    if faq_answer:
        add_message(conv_id, "user", body.question)
        add_message(conv_id, "assistant", faq_answer)
        return ChatResponse(answer=faq_answer, conversation_id=conv_id)

    messages = _build_messages(body.question, conv_id, user_ctx)
    final_answer = _resolve_tool_calls(messages, user_id=user_id)

    add_message(conv_id, "user", body.question)
    add_message(conv_id, "assistant", final_answer)

    return ChatResponse(answer=final_answer, conversation_id=conv_id)


# ── 端点2：流式 SSE ──

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, authorization: str = Header(None)):
    # 1) 从 JWT 提取用户身份
    user_ctx = _get_user_context(authorization)
    if not user_ctx:
        return ChatResponse(answer="请先登录后再使用AI客服。", conversation_id=None)
    user_id = user_ctx["user_id"]

    from services.conversation_service import create_conversation, add_message
    conv_id = body.conversation_id or create_conversation(user_id)

    # FAQ 优先检索：命中则直接流式返回预置答案，跳过 LLM
    faq_answer = search_faq(body.question)
    if faq_answer:
        add_message(conv_id, "user", body.question)
        add_message(conv_id, "assistant", faq_answer)
        return StreamingResponse(
            _event_stream_faq(faq_answer, conv_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    messages = _build_messages(body.question, conv_id, user_ctx)

    # 先完成工具调用轮次（同步，带 user_id）
    _resolve_tool_calls(messages, user_id=user_id)

    # 再流式输出 LLM 最终回答
    return StreamingResponse(
        _event_stream(messages, conv_id, body.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
