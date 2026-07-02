import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getOrderDetail, payOrder, cancelOrder, getPaymentStatus } from '../../api/order'
import { createReview } from '../../api/review'
import ReviewForm from '../../components/ReviewForm'
import type { Order, OrderItem, PaymentMethod } from '../../types'

const statusMap: Record<string, string> = { pending: '待支付', paid: '已支付', cancelled: '已取消' }
const statusBadge: Record<string, string> = { pending: 'badge-warning', paid: 'badge-success', cancelled: 'badge-gray' }

const PAYMENT_METHODS: { key: PaymentMethod; label: string; icon: string }[] = [
  { key: 'wechat', label: '微信支付', icon: '💚' },
  { key: 'alipay', label: '支付宝', icon: '💙' },
  { key: 'card', label: '银行卡', icon: '💳' },
]

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  // ── 支付（v2.0） ──
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('wechat')
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'failed'>('idle')

  // ── 评价（v2.0） ──
  const [reviewItem, setReviewItem] = useState<OrderItem | null>(null)

  const fetchOrder = async () => {
    if (!id) return
    const detail = await getOrderDetail(Number(id))
    if (detail.code === 0) setOrder(detail.data)
  }

  useEffect(() => {
    if (id) {
      setLoading(true)
      getOrderDetail(Number(id)).then(res => {
        if (res.code === 0) setOrder(res.data)
        setLoading(false)
      })
    }
  }, [id])

  const handlePaySubmit = async () => {
    if (!id) return
    setShowPaymentModal(false)
    setPaymentStatus('processing')
    try {
      const res = await payOrder(Number(id), paymentMethod)
      if (res.code !== 0) {
        setPaymentStatus('failed')
        alert(res.message)
        return
      }
      // 轮询支付状态（每 1s，10s 超时）
      const poll = setInterval(async () => {
        const status = await getPaymentStatus(Number(id))
        if (status.data?.status === 'success') {
          clearInterval(poll)
          setPaymentStatus('success')
          fetchOrder()
        } else if (status.data?.status === 'failed') {
          clearInterval(poll)
          setPaymentStatus('failed')
        }
      }, 1000)
      setTimeout(() => clearInterval(poll), 10000)
    } catch {
      setPaymentStatus('failed')
    }
  }

  const handleReviewSubmit = async (data: { product_id: number; order_id: number; rating: number; content: string }) => {
    const res = await createReview(data)
    if (res.code !== 0) throw new Error(res.message)
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
              {order.status === 'paid' && (
                <button
                  className="btn btn-outline btn-sm"
                  style={{ marginTop: 8 }}
                  onClick={() => setReviewItem(item)}
                >
                  去评价
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="card card-sm flex items-center justify-between" style={{ marginTop: '1rem' }}>
        <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>合计</span>
        <span className="product-card-price" style={{ fontSize: '1.5rem' }}>¥{order.total_amount}</span>
      </div>

      {/* 支付状态提示 */}
      {paymentStatus === 'processing' && (
        <div className="card card-sm" style={{ marginTop: '1rem', textAlign: 'center' }}>
          <div className="loading-dots"><span /><span /><span /></div>
          <p className="text-sm text-muted" style={{ marginTop: 8 }}>支付处理中，请稍候...</p>
        </div>
      )}
      {paymentStatus === 'failed' && (
        <div className="card card-sm" style={{ marginTop: '1rem', textAlign: 'center' }}>
          <p style={{ color: 'var(--rs-500, #ef4444)', marginBottom: 8 }}>❌ 支付失败</p>
          <button className="btn btn-primary btn-sm" onClick={() => setShowPaymentModal(true)}>重新支付</button>
        </div>
      )}

      {/* Actions */}
      <div className="btn-group" style={{ marginTop: '1.5rem' }}>
        {order.status === 'pending' && paymentStatus !== 'processing' && (
          <>
            <button className="btn btn-primary btn-lg" onClick={() => setShowPaymentModal(true)}>立即支付</button>
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

      {/* 支付方式选择弹窗 */}
      {showPaymentModal && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" onClick={e => e.stopPropagation()} style={{ width: '90%', maxWidth: 360 }}>
            <h3 style={{ marginTop: 0 }}>选择支付方式</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, margin: '16px 0' }}>
              {PAYMENT_METHODS.map(m => (
                <button
                  key={m.key}
                  onClick={() => setPaymentMethod(m.key)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                    borderRadius: 8, cursor: 'pointer', textAlign: 'left',
                    border: paymentMethod === m.key ? '2px solid #3b82f6' : '1px solid #d1d5db',
                    background: paymentMethod === m.key ? '#eff6ff' : '#fff',
                  }}
                >
                  <span style={{ fontSize: 20 }}>{m.icon}</span>
                  <span>{m.label}</span>
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-outline btn-sm" onClick={() => setShowPaymentModal(false)}>取消</button>
              <button className="btn btn-primary btn-sm" onClick={handlePaySubmit}>确认支付 ¥{order.total_amount}</button>
            </div>
          </div>
        </div>
      )}

      {/* 评价弹窗 */}
      {reviewItem && (
        <div className="modal-overlay" onClick={() => setReviewItem(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" onClick={e => e.stopPropagation()} style={{ width: '90%', maxWidth: 420, padding: 0 }}>
            <ReviewForm
              productId={reviewItem.product_id}
              orderId={order.id}
              productName={reviewItem.product_name}
              onSubmit={handleReviewSubmit}
              onClose={() => setReviewItem(null)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
