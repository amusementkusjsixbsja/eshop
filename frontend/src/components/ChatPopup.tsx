import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { chatStream } from '../api/aiChat'
import Markdown from 'react-markdown'
import './ChatPopup.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const PAYMENT_QUICK_OPTIONS: { method: string; label: string }[] = [
  { method: 'wechat', label: '💚 微信支付' },
  { method: 'alipay', label: '💙 支付宝' },
  { method: 'card', label: '💳 银行卡' },
  { method: 'balance', label: '💰 余额' },
]

/** 从 AI 文本中提取订单号（如「订单 #1024」「订单号 1024」「订单1024」） */
function extractOrderId(text: string): number | null {
  const m = text.match(/订单\s*(?:号|编号)?\s*#?\s*(\d{2,})/)
  return m ? Number(m[1]) : null
}

/** 判断 AI 文本是否在询问支付方式 */
function asksPaymentMethod(text: string): boolean {
  return /支付方式|选择.*(微信|支付宝|银行卡|余额)|如何支付|怎么支付/.test(text)
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
  const navigate = useNavigate()

  // ⚠ 临时：未登录时构造虚拟用户，方便前端调测 AI 接口
  const _user = user || { id: 1, name: '测试用户' }

  useEffect(() => { endRef.current?.scrollIntoView() }, [messages])

  // 最新一条 assistant 消息（用于判断是否展示支付快捷按钮）
  const lastMsg = messages[messages.length - 1]
  const showPaymentButtons =
    !loading && lastMsg?.role === 'assistant' && asksPaymentMethod(lastMsg.content)

  /** 判断是否处于"等待首个 token"的阶段（工具调用中） */
  const isWaitingFirstToken = loading && (
    messages.length === 0 ||
    messages[messages.length - 1].role !== 'assistant' ||
    messages[messages.length - 1].content === ''
  )

  const handleSend = async (overrideText?: string) => {
    const raw = overrideText ?? input
    if (!raw.trim() || loading) return

    const question = raw.trim()
    if (overrideText === undefined) setInput('')
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
            {messages.map((m, i) => {
              const orderId = m.role === 'assistant' ? extractOrderId(m.content) : null
              return (
                <div key={i} className={`chat-message-row ${m.role}`}>
                  <span className={`chat-bubble ${m.role}`}>
                    {m.role === 'user'
                      ? m.content
                      : <span className="markdown-content"><Markdown>{m.content}</Markdown></span>
                    }
                    {orderId && (
                      <div className="order-card" onClick={() => { setOpen(false); navigate(`/orders/${orderId}`) }}>
                        <div>📦 订单 #{orderId}</div>
                        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>点击查看订单详情 →</div>
                      </div>
                    )}
                  </span>
                </div>
              )
            })}
            {/* 仅在工具调用阶段显示加载提示 */}
            {isWaitingFirstToken && <div className="chat-loading">AI 正在思考...</div>}
            <div ref={endRef} />
          </div>
          {/* 支付方式快捷按钮：AI 询问支付方式时展示 */}
          {showPaymentButtons && (
            <div className="payment-quick-buttons">
              {PAYMENT_QUICK_OPTIONS.map(opt => (
                <button key={opt.method} onClick={() => handleSend(`使用${opt.label.replace(/^\S+\s*/, '')}`)}>
                  {opt.label}
                </button>
              ))}
            </div>
          )}
          <div className="chat-input-bar">
            <input
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder={_user ? '输入问题...' : '请先登录'}
              disabled={!_user}
              className="chat-input"
            />
            <button onClick={() => handleSend()} disabled={loading || !_user} className="chat-send-btn">
              发送
            </button>
          </div>
        </div>
      )}
    </>
  )
}
