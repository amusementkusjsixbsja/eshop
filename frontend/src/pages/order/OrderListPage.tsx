import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listOrders } from '../../api/order'
import type { Order } from '../../types'

export default function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => { loadOrders() }, [filter])

  const loadOrders = async () => {
    const res = await listOrders({ status: filter || undefined })
    if (res.code === 0) setOrders(res.data.items)
  }

  const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h1>我的订单 <Link to="/products">继续购物</Link></h1>
      <div style={{ margin: '8px 0', display: 'flex', gap: 8 }}>
        {['', 'pending', 'paid', 'cancelled'].map(s => (
          <button key={s} onClick={() => setFilter(s)}>{s ? statusMap[s] : '全部'}</button>
        ))}
      </div>
      {orders.map(o => (
        <Link key={o.id} to={`/orders/${o.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8, margin: '8px 0' }}>
            <div>订单 #{o.id}</div>
            <div>金额：¥{o.total_amount} | 状态：{statusMap[o.status] || o.status}</div>
            <div style={{ color: '#999', fontSize: 12 }}>{o.created_at}</div>
          </div>
        </Link>
      ))}
    </div>
  )
}
