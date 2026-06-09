import { useState, useRef, useEffect } from 'react'
import { chatStream } from '../api/aiChat'
import Markdown from 'react-markdown'
import './ChatPopup.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPopup({ user }: { user: any }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '您好！我是 AI 客服助手，可以帮您查询订单、物流等信息，或解答常见问题。' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const convIdRef = useRef<string | null>(null)

  // ⚠ 临时：未登录时构造虚拟用户，方便前端调测 AI 接口
  const _user = user || { id: 1, name: '测试用户' }

  useEffect(() => { endRef.current?.scrollIntoView() }, [messages])

  /** 判断是否处于"等待首个 token"的阶段（工具调用中） */
  const isWaitingFirstToken = loading && (
    messages.length === 0 ||
    messages[messages.length - 1].role !== 'assistant' ||
    messages[messages.length - 1].content === ''
  )

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      // 先插入空占位消息，流式 token 到达后逐字追加
      setMessages(prev => [...prev, { role: 'assistant', content: '' }])

      await chatStream(
        question,
        convIdRef.current || undefined,
        // onToken: 追加到最后一个 assistant 消息
        (token) => {
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            if (last.role === 'assistant') {
              updated[updated.length - 1] = { ...last, content: last.content + token }
            }
            return updated
          })
        },
        // onMeta: 保存 conversation_id
        (meta) => {
          if (meta.conversation_id) convIdRef.current = meta.conversation_id
        },
      )
    } catch {
      // 流式失败：替换占位消息为错误提示
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last.role === 'assistant' && !last.content) {
          updated[updated.length - 1] = { role: 'assistant', content: '抱歉，服务暂时不可用，请稍后再试。' }
        } else {
          updated.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后再试。' })
        }
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* 浮窗按钮 */}
      <button
        onClick={() => setOpen(!open)}
        className="chat-toggle-btn"
      >
        {open ? '✕' : '💬'}
      </button>

      {/* 对话面板 */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            AI
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-message-row ${m.role}`}>
                <span className={`chat-bubble ${m.role}`}>
                  {m.role === 'user'
                    ? m.content
                    : <span className="markdown-content"><Markdown>{m.content}</Markdown></span>
                  }
                </span>
              </div>
            ))}
            {/* 仅在工具调用阶段显示加载提示 */}
            {isWaitingFirstToken && <div className="chat-loading">AI 正在思考...</div>}
            <div ref={endRef} />
          </div>
          <div className="chat-input-bar">
            <input
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder={_user ? '输入问题...' : '请先登录'}
              disabled={!_user}
              className="chat-input"
            />
            <button onClick={handleSend} disabled={loading || !_user} className="chat-send-btn">
              发送
            </button>
          </div>
        </div>
      )}
    </>
  )
}
