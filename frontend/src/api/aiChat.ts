import type { ChatResponse } from '../types'

const AI_BASE = '/api/ai'

/** 临时测试用假 JWT — 见 test_llm.py 绕过登录 */
const FAKE_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InRlc3RAZXNob3AuY29tIiwicm9sZSI6InVzZXIifQ.fake-signature'

/**
 * AI 对话（非流式）— 直接使用 fetch 而非 axios 客户端，
 * 因为 AI 服务使用独立的 baseURL。
 */
export async function chat(question: string, conversation_id?: string): Promise<ChatResponse> {
  const token = localStorage.getItem('token') || FAKE_TOKEN

  const response = await fetch(`${AI_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, conversation_id }),
  })

  const data = await response.json() as ChatResponse
  return {
    answer: data.answer || '服务暂不可用',
    conversation_id: data.conversation_id,
  }
}

/**
 * AI 对话（流式 SSE）— 逐 token 回调 onToken，适用于实时打字效果。
 */
export async function chatStream(
  question: string,
  conversation_id: string | undefined,
  onToken: (token: string) => void,
  onMeta?: (meta: { conversation_id: string }) => void,
): Promise<void> {
  const token = localStorage.getItem('token') || FAKE_TOKEN

  const response = await fetch(`${AI_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, conversation_id }),
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  // 解析 SSE text/event-stream
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''  // 保留可能不完整的行

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()

        // 结束标记
        if (data === '[DONE]') return

        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'token' && parsed.content) {
            onToken(parsed.content)
          } else if (parsed.type === 'meta' && onMeta && parsed.conversation_id) {
            onMeta({ conversation_id: parsed.conversation_id })
          }
        } catch {
          // 忽略解析失败的碎片数据
        }
      }
    }
  }
}
