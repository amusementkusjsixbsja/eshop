import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCart, updateCartItem, deleteCartItem } from '../../api/cart'
import { createOrder } from '../../api/order'
import { listAddresses } from '../../api/address'
import type { CartItem } from '../../types'
import type { Address } from '../../api/address'

export default function CartPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<CartItem[]>([])
  const [addresses, setAddresses] = useState<Address[]>([])
  const [selectedAddressId, setSelectedAddressId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [ordering, setOrdering] = useState(false)

  useEffect(() => {
    Promise.all([loadCart(), loadAddresses()])
  }, [])

  const loadCart = async () => {
    setLoading(true)
    try {
      const res = await getCart()
      if (res.code === 0) setItems(res.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  const loadAddresses = async () => {
    try {
      const res = await listAddresses()
      if (res.code === 0) {
        const list = res.data.items || []
        setAddresses(list)
        // 默认选中默认地址
        const def = list.find(a => a.is_default)
        if (def) setSelectedAddressId(def.id)
        else if (list.length > 0) setSelectedAddressId(list[0].id)
      }
    } catch {}
  }

  const handleCheckout = async () => {
    const addr = addresses.find(a => a.id === selectedAddressId)
    if (!addr) return alert('请选择收货地址')
    setOrdering(true)
    try {
      const res = await createOrder(addr.address)
      if (res.code === 0) {
        navigate(`/orders/${res.data.id}`)
      } else {
        alert(res.message)
      }
    } finally {
      setOrdering(false)
    }
  }

  const handleQuantity = async (product_id: number, delta: number) => {
    const item = items.find(i => i.product_id === product_id)
    if (!item) return
    const newQty = item.quantity + delta
    if (newQty < 1 || newQty > item.stock) return
    await updateCartItem(product_id, newQty)
    loadCart()
  }

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0)

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>🛒 购物车</h1>
        <button className="btn btn-ghost" onClick={() => navigate('/products')}>继续购物</button>
      </div>

      {loading ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : items.length === 0 ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">🛒</div>
          <p className="state-title">购物车是空的</p>
          <p className="state-desc">快去挑选心仪的商品吧</p>
          <button className="btn btn-primary" onClick={() => navigate('/products')}>去逛逛</button>
        </div>
      ) : (
        <>
          <div className="card" style={{ padding: 0 }}>
            {items.map((item, i) => (
              <div key={item.product_id} className="cart-item animate-in" style={{ animationDelay: `${i * 0.04}s` }}>
                <div className="cart-item-info">
                  <div className="cart-item-name">{item.name}</div>
                  <div className="cart-item-price" style={{ marginTop: 4 }}>¥{item.price}</div>
                </div>
                <div className="qty-control">
                  <button onClick={() => handleQuantity(item.product_id, -1)} disabled={item.quantity <= 1}>−</button>
                  <span>{item.quantity}</span>
                  <button onClick={() => handleQuantity(item.product_id, 1)} disabled={item.quantity >= item.stock}>+</button>
                </div>
                <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', minWidth: 70, textAlign: 'right' }}>
                  ¥{(item.price * item.quantity).toFixed(2)}
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  style={{ color: 'var(--rs-500)' }}
                  onClick={() => deleteCartItem(item.product_id).then(loadCart)}
                >删除</button>
              </div>
            ))}
          </div>

          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="flex items-center justify-between" style={{ marginBottom: '1rem' }}>
              <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>合计</span>
              <span className="product-card-price" style={{ fontSize: '1.5rem' }}>¥{total.toFixed(2)}</span>
            </div>

            {/* Address selector */}
            <div className="form-group">
              <label className="form-label">收货地址</label>
              {addresses.length > 0 ? (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  {addresses.map(a => (
                    <div
                      key={a.id}
                      onClick={() => setSelectedAddressId(a.id)}
                      style={{
                        flex: 1, minWidth: 180, padding: '10px 14px',
                        border: `2px solid ${selectedAddressId === a.id ? 'var(--color-primary)' : 'var(--color-border)'}`,
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        background: selectedAddressId === a.id ? 'var(--em-50)' : '#fff',
                        transition: 'all var(--transition)',
                      }}
                    >
                      <div className="flex items-center gap-xs" style={{ marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{a.name}</span>
                        {a.label && <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>{a.label}</span>}
                        {a.is_default && <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>默认</span>}
                      </div>
                      <div className="text-sm text-muted">{a.phone}</div>
                      <div className="text-sm text-muted">{a.address}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted" style={{ marginBottom: 8 }}>
                  暂无地址，
                  <a href="/addresses" onClick={(e) => { e.preventDefault(); navigate('/addresses') }}>去添加</a>
                </p>
              )}
              <a href="/addresses" onClick={(e) => { e.preventDefault(); navigate('/addresses') }}
                style={{ fontSize: '0.85rem' }}>管理地址 →</a>
            </div>

            <button
              className="btn btn-primary btn-lg btn-block"
              onClick={handleCheckout}
              disabled={ordering || items.length === 0 || !selectedAddressId}
            >
              {ordering ? '提交中...' : '结算'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
