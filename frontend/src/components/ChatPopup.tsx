import { useState, useRef, useEffect } from 'react'
import { chat } from '../api/aiChat'

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

  useEffect(() => { endRef.current?.scrollIntoView() }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    if (!user) { alert('请先登录后再咨询 AI 客服'); return }

    const question = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const res = await chat(question)
      setMessages(prev => [...prev, { role: 'assistant', content: res.answer }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，服务暂时不可用，请稍后再试。' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* 浮窗按钮 */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 1000,
          width: 56, height: 56, borderRadius: '50%', background: '#1890ff',
          color: '#fff', border: 'none', fontSize: 24, cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}
      >
        {open ? '✕' : '💬'}
      </button>

      {/* 对话面板 */}
      {open && (
        <div style={{
          position: 'fixed', bottom: 90, right: 24, zIndex: 1000,
          width: 360, height: 500, background: '#fff', borderRadius: 12,
          boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
          display: 'flex', flexDirection: 'column',
        }}>
          <div style={{ padding: 12, background: '#1890ff', color: '#fff', borderRadius: '12px 12px 0 0', fontWeight: 'bold' }}>
            AI 客服助手
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ margin: '8px 0', textAlign: m.role === 'user' ? 'right' : 'left' }}>
                <span style={{
                  display: 'inline-block', padding: '8px 12px', borderRadius: 8, maxWidth: '80%',
                  background: m.role === 'user' ? '#1890ff' : '#f0f0f0',
                  color: m.role === 'user' ? '#fff' : '#333',
                  whiteSpace: 'pre-wrap',
                }}>{m.content}</span>
              </div>
            ))}
            {loading && <div style={{ color: '#999' }}>AI 正在思考...</div>}
            <div ref={endRef} />
          </div>
          <div style={{ padding: 8, borderTop: '1px solid #eee', display: 'flex' }}>
            <input
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder={user ? '输入问题...' : '请先登录'}
              disabled={!user}
              style={{ flex: 1, padding: 8, border: '1px solid #ddd', borderRadius: 4, marginRight: 8 }}
            />
            <button onClick={handleSend} disabled={loading || !user} style={{ padding: '8px 16px', background: '#1890ff', color: '#fff', border: 'none', borderRadius: 4 }}>
              发送
            </button>
          </div>
        </div>
      )}
    </>
  )
}
