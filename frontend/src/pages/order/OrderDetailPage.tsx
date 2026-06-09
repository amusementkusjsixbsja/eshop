import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getOrderDetail, payOrder, cancelOrder } from '../../api/order'
import type { Order } from '../../types'

const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }
const statusBadge: Record<string, string> = { pending: 'badge-warning', paid: 'badge-success', cancelled: 'badge-gray' }

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      setLoading(true)
      getOrderDetail(Number(id)).then(res => {
        if (res.code === 0) setOrder(res.data)
        setLoading(false)
      })
    }
  }, [id])

  const handlePay = async () => {
    if (!id) return
    const res = await payOrder(Number(id))
    if (res.code === 0) {
      // 重新获取完整订单信息（pay_order 返回最小数据）
      const detail = await getOrderDetail(Number(id))
      if (detail.code === 0) setOrder(detail.data)
    } else {
      alert(res.message)
    }
  }

  const handleCancel = async () => {
    if (!id) return
    if (!confirm('确定要取消这个订单吗？')) return
    const res = await cancelOrder(Number(id))
    if (res.code === 0) {
      const detail = await getOrderDetail(Number(id))
      if (detail.code === 0) setOrder(detail.data)
    } else {
      alert(res.message)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="page">
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">🔍</div>
          <p className="state-title">订单不存在</p>
          <button className="btn btn-outline" onClick={() => navigate('/orders')}>返回订单列表</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page animate-in">
      <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} style={{ marginBottom: '1rem' }}>
        ← 返回
      </button>

      <div className="page-header">
        <h1>订单 #{order.id}</h1>
        <span className={`badge ${statusBadge[order.status] || 'badge-gray'}`} style={{ fontSize: '0.9rem', padding: '4px 16px' }}>
          {statusMap[order.status] || order.status}
        </span>
      </div>

      {/* Order Info */}
      <div className="card card-sm" style={{ marginBottom: '1rem' }}>
        <div className="detail-row">
          <span className="detail-label">订单编号</span>
          <span className="detail-value">#{order.id}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">创建时间</span>
          <span className="detail-value">{order.created_at}</span>
        </div>
        {order.paid_at && (
          <div className="detail-row">
            <span className="detail-label">支付时间</span>
            <span className="detail-value">{order.paid_at}</span>
          </div>
        )}
        <div className="detail-row">
          <span className="detail-label">收货地址</span>
          <span className="detail-value">{order.address}</span>
        </div>
      </div>

      {/* Order Items */}
      <h3 style={{ marginBottom: '0.75rem' }}>商品明细</h3>
      <div className="card" style={{ padding: 0 }}>
        {order.items?.map((item, i) => (
          <div key={item.id} className="cart-item animate-in" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="cart-item-info">
              <div className="cart-item-name">{item.product_name}</div>
              <div className="text-sm text-muted" style={{ marginTop: 2 }}>商品 #{item.product_id}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div>¥{item.price} × {item.quantity}</div>
              <div className="text-sm text-muted" style={{ marginTop: 2 }}>
                小计: <span className="font-semibold">¥{(item.price * item.quantity).toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="card card-sm flex items-center justify-between" style={{ marginTop: '1rem' }}>
        <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>合计</span>
        <span className="product-card-price" style={{ fontSize: '1.5rem' }}>¥{order.total_amount}</span>
      </div>

      {/* Actions */}
      <div className="btn-group" style={{ marginTop: '1.5rem' }}>
        {order.status === 'pending' && (
          <>
            <button className="btn btn-primary btn-lg" onClick={handlePay}>立即支付</button>
            <button className="btn btn-outline btn-lg" onClick={handleCancel}>取消订单</button>
          </>
        )}
        {order.status === 'paid' && (
          <>
            <Link to={`/logistics/${order.id}`}>
              <button className="btn btn-primary">查看物流</button>
            </Link>
            <Link to="/after-sales">
              <button className="btn btn-outline">申请售后</button>
            </Link>
          </>
        )}
      </div>
    </div>
  )
}
