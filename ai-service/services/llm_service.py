"""★ 小A：LLM 调用服务。

当前 AI 回复使用模板字符串拼接（chat_router.py 中已实现）。

如需集成真实 LLM：
  1. 选择一个 LLM API（OpenAI / Claude / 本地模型）
  2. 在此处封装调用
  3. 设计 system prompt（包含角色设定 + 可用的内部接口信息）
  4. 将 chat_router.py 中的模板替换为 LLM 调用

示例：
```python
import httpx

LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

def chat_with_llm(system_prompt: str, user_message: str) -> str:
    response = httpx.post(
        LLM_API_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        },
    )
    return response.json()["choices"][0]["message"]["content"]
```
"""
