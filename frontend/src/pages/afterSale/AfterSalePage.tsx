import { useEffect, useState } from 'react'
import { listAfterSales, createAfterSale } from '../../api/afterSale'
import type { AfterSale } from '../../types'

const typeMap: Record<string, string> = { refund: '退款', return: '退货', exchange: '换货' }
const statusMap: Record<string, string> = { pending: '待处理', approved: '已通过', rejected: '已拒绝', completed: '已完成' }

export default function AfterSalePage() {
  const [items, setItems] = useState<AfterSale[]>([])
  const [orderId, setOrderId] = useState('')
  const [type, setType] = useState<'refund' | 'return'>('refund')
  const [reason, setReason] = useState('')

  useEffect(() => { load() }, [])

  const load = async () => {
    const res = await listAfterSales()
    if (res.code === 0) setItems(res.data.items || [])
  }

  const handleSubmit = async () => {
    if (!orderId) return alert('请输入订单号')
    const res = await createAfterSale(Number(orderId), type, reason)
    if (res.code === 0) {
      alert('售后申请已提交')
      load()
      setOrderId('')
      setReason('')
    } else {
      alert(res.message)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h1>售后中心</h1>
      <div style={{ border: '1px solid #eee', borderRadius: 8, padding: 16, marginBottom: 24 }}>
        <h3>申请售后</h3>
        <input placeholder="订单ID" value={orderId} onChange={e => setOrderId(e.target.value)} style={{ width: '100%', padding: 8, margin: '4px 0' }} />
        <select value={type} onChange={e => setType(e.target.value as any)} style={{ width: '100%', padding: 8, margin: '4px 0' }}>
          <option value="refund">退款</option>
          <option value="return">退货</option>
        </select>
        <textarea placeholder="原因（可选）" value={reason} onChange={e => setReason(e.target.value)} style={{ width: '100%', padding: 8, margin: '4px 0' }} />
        <button onClick={handleSubmit} style={{ padding: '8px 24px', background: '#ff4d4f', color: '#fff', border: 'none', borderRadius: 4 }}>提交申请</button>
      </div>
      <h3>我的售后申请</h3>
      {items.map(a => (
        <div key={a.id} style={{ padding: 12, border: '1px solid #eee', borderRadius: 8, margin: '8px 0' }}>
          <div>#{a.id} 订单 #{a.order_id} | {typeMap[a.type] || a.type} | {statusMap[a.status] || a.status}</div>
          <div style={{ color: '#999', fontSize: 12 }}>{a.created_at}</div>
          {a.reason && <div style={{ color: '#666' }}>原因：{a.reason}</div>}
        </div>
      ))}
    </div>
  )
}
