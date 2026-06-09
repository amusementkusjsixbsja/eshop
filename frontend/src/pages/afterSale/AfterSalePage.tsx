import { useEffect, useState } from 'react'
import { listAfterSales, createAfterSale } from '../../api/afterSale'
import type { AfterSale } from '../../types'

const typeMap: Record<string, string> = { refund: '退款', return: '退货', exchange: '换货' }
const statusBadge: Record<string, string> = { pending: 'badge-warning', approved: 'badge-success', rejected: 'badge-danger', completed: 'badge-gray' }
const statusText: Record<string, string> = { pending: '待处理', approved: '已通过', rejected: '已拒绝', completed: '已完成' }

export default function AfterSalePage() {
  const [items, setItems] = useState<AfterSale[]>([])
  const [orderId, setOrderId] = useState('')
  const [type, setType] = useState<'refund' | 'return'>('refund')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await listAfterSales()
      if (res.code === 0) setItems(res.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!orderId) return alert('请输入订单号')
    setSubmitting(true)
    try {
      const res = await createAfterSale(Number(orderId), type, reason)
      if (res.code === 0) {
        alert('售后申请已提交')
        load()
        setOrderId(''); setReason('')
      } else {
        alert(res.message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>🔧 售后中心</h1>
      </div>

      {/* Apply form */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>申请售后</h3>
        <div className="form-group">
          <label className="form-label">订单号</label>
          <input className="input" type="number" placeholder="输入订单 ID" value={orderId} onChange={e => setOrderId(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">售后类型</label>
          <select className="input" value={type} onChange={e => setType(e.target.value as any)}>
            <option value="refund">退款</option>
            <option value="return">退货</option>
            <option value="exchange">换货</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">原因</label>
          <textarea className="input" placeholder="请描述您的售后原因（可选）" value={reason} onChange={e => setReason(e.target.value)} rows={3} />
        </div>
        <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
          {submitting ? '提交中...' : '提交申请'}
        </button>
      </div>

      {/* History */}
      <h3 style={{ marginBottom: '1rem' }}>我的售后申请</h3>
      {loading ? (
        <div className="state" style={{ minHeight: 150 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : items.length === 0 ? (
        <div className="state" style={{ minHeight: 150 }}>
          <p className="state-desc">暂无售后记录</p>
        </div>
      ) : (
        <div>
          {items.map((a, i) => (
            <div key={a.id} className="card card-hover animate-in" style={{ animationDelay: `${i * 0.05}s`, marginBottom: '0.75rem' }}>
              <div className="flex items-center justify-between" style={{ marginBottom: 6 }}>
                <span style={{ fontWeight: 600 }}>#{a.id} — 订单 #{a.order_id}</span>
                <span className={`badge ${statusBadge[a.status] || 'badge-gray'}`}>{statusText[a.status] || a.status}</span>
              </div>
              <div className="flex items-center gap-sm text-sm text-muted">
                <span className="badge badge-primary">{typeMap[a.type] || a.type}</span>
                <span>{a.created_at}</span>
              </div>
              {a.reason && (
                <div className="text-sm" style={{ marginTop: 6, color: 'var(--gray-600)' }}>
                  原因：{a.reason}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
