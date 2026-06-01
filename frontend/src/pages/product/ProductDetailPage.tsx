import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProductDetail } from '../../api/product'
import { addToCart } from '../../api/cart'
import type { Product } from '../../types'

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState<Product | null>(null)
  const [qty, setQty] = useState(1)

  useEffect(() => {
    if (id) getProductDetail(Number(id)).then(res => res.code === 0 && setProduct(res.data))
  }, [id])

  const handleAddToCart = async () => {
    if (!product) return
    const res = await addToCart(product.id, qty)
    if (res.code === 0) {
      alert('已加入购物车')
      navigate('/cart')
    } else {
      alert(res.message)
    }
  }

  if (!product) return <div style={{ padding: 20 }}>加载中...</div>

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <button onClick={() => navigate(-1)}>← 返回</button>
      <div style={{ display: 'flex', gap: 32, marginTop: 16 }}>
        <img src={product.image_url} alt={product.name} style={{ width: 300, height: 300, objectFit: 'cover', borderRadius: 8 }} />
        <div>
          <h1>{product.name}</h1>
          <p style={{ color: '#f5222d', fontSize: 28, fontWeight: 'bold' }}>¥{product.price}</p>
          <p>{product.description}</p>
          <p>库存：{product.stock} 件</p>
          <div style={{ margin: '16px 0', display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={() => setQty(Math.max(1, qty - 1))}>-</button>
            <span>{qty}</span>
            <button onClick={() => setQty(Math.min(product.stock, qty + 1))}>+</button>
          </div>
          <button onClick={handleAddToCart} style={{ padding: '12px 32px', background: '#ff4d4f', color: '#fff', border: 'none', borderRadius: 4, fontSize: 16 }}>
            加入购物车
          </button>
        </div>
      </div>
    </div>
  )
}
