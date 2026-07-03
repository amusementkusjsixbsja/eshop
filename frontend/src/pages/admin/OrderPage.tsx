import { useEffect, useState } from 'react'
import { adminListOrders } from '../../api/admin'
import type { Order } from '../../types'

const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }
const statusBadge: Record<string, string> = { pending: 'badge-warning', paid: 'badge-success', cancelled: 'badge-gray' }

export default function AdminOrderPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [filter])

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminListOrders({ status: filter || undefined })
      if (res.code === 0) setOrders(res.data.items)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-content animate-in">
        <div className="page-header">
          <h1>订单管理</h1>
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
            <p className="state-desc">{filter ? `没有${statusMap[filter]}的订单` : '系统暂无订单数据'}</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>订单号</th>
                  <th>用户</th>
                  <th>金额</th>
                  <th>状态</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>#{o.id}</td>
                    <td>
                      <span className="badge badge-gray">UID: {o.user_id}</span>
                    </td>
                    <td className="product-card-price" style={{ fontSize: '1rem' }}>¥{o.total_amount}</td>
                    <td><span className={`badge ${statusBadge[o.status] || 'badge-gray'}`}>{statusMap[o.status] || o.status}</span></td>
                    <td className="text-sm text-muted">{o.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </div>
  )
}
