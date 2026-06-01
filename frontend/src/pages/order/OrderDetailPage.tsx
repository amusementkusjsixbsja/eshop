import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getOrderDetail, payOrder, cancelOrder } from '../../api/order'
import type { Order } from '../../types'

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)

  useEffect(() => {
    if (id) getOrderDetail(Number(id)).then(res => res.code === 0 && setOrder(res.data))
  }, [id])

  const handlePay = async () => {
    if (!id) return
    const res = await payOrder(Number(id))
    if (res.code === 0) setOrder(res.data)
    else alert(res.message)
  }

  const handleCancel = async () => {
    if (!id) return
    const res = await cancelOrder(Number(id))
    if (res.code === 0) setOrder(res.data)
    else alert(res.message)
  }

  if (!order) return <div style={{ padding: 20 }}>加载中...</div>

  const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <button onClick={() => navigate(-1)}>← 返回</button>
      <h1>订单 #{order.id}</h1>
      <p>状态：{statusMap[order.status]}</p>
      <p>收货地址：{order.address}</p>
      <p>创建时间：{order.created_at}</p>
      <h3>商品明细</h3>
      {order.items?.map(item => (
        <div key={item.id} style={{ display: 'flex', gap: 16, padding: 8, borderBottom: '1px solid #eee' }}>
          <span>{item.product_name}</span>
          <span>¥{item.price} × {item.quantity}</span>
        </div>
      ))}
      <p style={{ fontSize: 20, fontWeight: 'bold', marginTop: 16 }}>合计：¥{order.total_amount}</p>
      <div style={{ display: 'flex', gap: 8 }}>
        {order.status === 'pending' && <><button onClick={handlePay} style={{ padding: '10px 24px', background: '#52c41a', color: '#fff', border: 'none', borderRadius: 4 }}>立即支付</button><button onClick={handleCancel} style={{ padding: '10px 24px', background: '#999', color: '#fff', border: 'none', borderRadius: 4 }}>取消订单</button></>}
        {order.status === 'paid' && <Link to={`/logistics/${order.id}`}><button style={{ padding: '10px 24px' }}>查看物流</button></Link>}
        {order.status === 'paid' && <Link to="/after-sales"><button style={{ padding: '10px 24px' }}>申请售后</button></Link>}
      </div>
    </div>
  )
}
