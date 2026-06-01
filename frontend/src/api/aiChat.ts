import type { ApiResponse, ChatResponse } from '../types'

const AI_BASE = '/api/ai'

/**
 * AI 对话 — 直接使用 fetch 而非 axios 客户端，
 * 因为 AI 服务使用独立的 baseURL。
 */
export async function chat(question: string, conversation_id?: string): Promise<ChatResponse> {
  const token = localStorage.getItem('token')

  const response = await fetch(`${AI_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, conversation_id }),
  })

  const data = await response.json() as ApiResponse<ChatResponse>
  return data.data || { answer: data.message || '服务暂不可用' }
}
