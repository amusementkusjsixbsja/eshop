import { useEffect, useState } from 'react'
import { adminListOrders } from '../../api/admin'
import type { Order } from '../../types'

const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }

export default function AdminOrderPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => { load() }, [filter])

  const load = async () => {
    const res = await adminListOrders({ status: filter || undefined })
    if (res.code === 0) setOrders(res.data.items)
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 20 }}>
      <h1>订单管理</h1>
      <div style={{ margin: '8px 0', display: 'flex', gap: 8 }}>
        {['', 'pending', 'paid', 'cancelled'].map(s => (
          <button key={s} onClick={() => setFilter(s)}>{s ? statusMap[s] : '全部'}</button>
        ))}
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr><th>ID</th><th>用户</th><th>金额</th><th>状态</th><th>时间</th></tr></thead>
        <tbody>
          {orders.map(o => (
            <tr key={o.id}><td>{o.id}</td><td>{o.user_id}</td><td>¥{o.total_amount}</td><td>{statusMap[o.status] || o.status}</td><td>{o.created_at}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
