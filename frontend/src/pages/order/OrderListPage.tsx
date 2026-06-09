import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listOrders } from '../../api/order'
import type { Order } from '../../types'

const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }
const statusBadge: Record<string, string> = { pending: 'badge-warning', paid: 'badge-success', cancelled: 'badge-gray' }

export default function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadOrders() }, [filter])

  const loadOrders = async () => {
    setLoading(true)
    try {
      const res = await listOrders({ status: filter || undefined })
      if (res.code === 0) setOrders(res.data.items)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>📋 我的订单</h1>
        <Link to="/products" className="btn btn-ghost btn-sm">继续购物</Link>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: '1.5rem', borderBottom: '2px solid var(--color-border)', paddingBottom: 0 }}>
        {['', 'pending', 'paid', 'cancelled'].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: '8px 20px',
              background: 'none',
              border: 'none',
              borderBottom: filter === s ? '2px solid var(--color-primary)' : '2px solid transparent',
              marginBottom: '-2px',
              color: filter === s ? 'var(--color-primary)' : 'var(--gray-500)',
              fontWeight: filter === s ? 600 : 400,
              cursor: 'pointer',
              transition: 'all var(--transition)',
              fontSize: '0.9rem',
            }}
          >{s ? statusMap[s] : '全部'}</button>
        ))}
      </div>

      {loading ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : orders.length === 0 ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">📄</div>
          <p className="state-title">暂无订单</p>
          <p className="state-desc">{filter ? `没有${statusMap[filter]}的订单` : '您还没有下过订单'}</p>
          <Link to="/products" className="btn btn-primary">去购物</Link>
        </div>
      ) : (
        <div>
          {orders.map((o, i) => (
            <Link key={o.id} to={`/orders/${o.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="card card-hover animate-in" style={{ animationDelay: `${i * 0.05}s`, marginBottom: '0.75rem' }}>
                <div className="flex items-center justify-between" style={{ marginBottom: 6 }}>
                  <span style={{ fontWeight: 600 }}>订单 #{o.id}</span>
                  <span className={`badge ${statusBadge[o.status] || 'badge-gray'}`}>{statusMap[o.status] || o.status}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted">{o.created_at}</span>
                  <span className="product-card-price">¥{o.total_amount}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
