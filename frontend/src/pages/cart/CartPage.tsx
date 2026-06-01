import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCart, updateCartItem, deleteCartItem } from '../../api/cart'
import { createOrder } from '../../api/order'
import type { CartItem } from '../../types'

export default function CartPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<CartItem[]>([])
  const [address, setAddress] = useState('广东省深圳市南山区')

  useEffect(() => { loadCart() }, [])

  const loadCart = async () => {
    const res = await getCart()
    if (res.code === 0) setItems(res.data.items || [])
  }

  const handleCheckout = async () => {
    const res = await createOrder(address)
    if (res.code === 0) {
      navigate(`/orders/${res.data.id}`)
    } else {
      alert(res.message)
    }
  }

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0)

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h1>购物车 <button onClick={() => navigate('/products')}>继续购物</button></h1>
      {items.map(item => (
        <div key={item.product_id} style={{ display: 'flex', gap: 16, padding: 12, borderBottom: '1px solid #eee', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>{item.name}</div>
          <div>¥{item.price}</div>
          <div>
            <button onClick={() => updateCartItem(item.product_id, Math.max(1, item.quantity - 1)).then(loadCart)}>-</button>
            <span style={{ margin: '0 8px' }}>{item.quantity}</span>
            <button onClick={() => updateCartItem(item.product_id, Math.min(item.stock, item.quantity + 1)).then(loadCart)}>+</button>
          </div>
          <button onClick={() => deleteCartItem(item.product_id).then(loadCart)} style={{ color: 'red' }}>删除</button>
        </div>
      ))}
      <div style={{ marginTop: 16 }}>
        <p>合计：¥{total.toFixed(2)}</p>
        <div><input value={address} onChange={e => setAddress(e.target.value)} style={{ width: '100%', padding: 8 }} placeholder="收货地址" /></div>
        <button onClick={handleCheckout} style={{ marginTop: 8, padding: '12px 32px', background: '#1890ff', color: '#fff', border: 'none', borderRadius: 4 }} disabled={items.length === 0}>
          结算
        </button>
      </div>
    </div>
  )
}
