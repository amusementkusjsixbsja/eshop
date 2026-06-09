import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProductDetail } from '../../api/product'
import { addToCart } from '../../api/cart'
import type { Product } from '../../types'

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [qty, setQty] = useState(1)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (id) {
      setLoading(true)
      getProductDetail(Number(id)).then(res => {
        if (res.code === 0) setProduct(res.data)
        setLoading(false)
      })
    }
  }, [id])

  const handleAddToCart = async () => {
    if (!product) return
    setAdding(true)
    try {
      const res = await addToCart(product.id, qty)
      if (res.code === 0) {
        navigate('/cart')
      } else {
        alert(res.message)
      }
    } finally {
      setAdding(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="state" style={{ minHeight: 400 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="page">
        <div className="state" style={{ minHeight: 400 }}>
          <div className="state-icon">🔍</div>
          <p className="state-title">商品不存在</p>
          <p className="state-desc">该商品可能已下架或已删除</p>
          <button className="btn btn-outline" onClick={() => navigate(-1)}>返回</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page animate-in">
      <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} style={{ marginBottom: '1rem' }}>
        ← 返回
      </button>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Image */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'sticky', top: 80 }}>
          <img
            src={product.image_url}
            alt={product.name}
            style={{ width: '100%', height: 'auto', aspectRatio: '1', objectFit: 'cover' }}
            onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/600?text=' + product.name }}
          />
        </div>

        {/* Info */}
        <div>
          <h1>{product.name}</h1>
          <p className="text-sm text-muted" style={{ marginTop: 8 }}>{product.description}</p>

          <div style={{ margin: '1.5rem 0', padding: '1rem 0', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}>
            <span className="product-card-price" style={{ fontSize: '2rem' }}>¥{product.price}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">分类</span>
            <span className="detail-value">{product.category_name || '-'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">库存</span>
            <span className="detail-value">
              {product.stock > 0 ? (
                <span style={{ color: 'var(--em-600)', fontWeight: 600 }}>有货 ({product.stock} 件)</span>
              ) : (
                <span style={{ color: 'var(--rs-500)', fontWeight: 600 }}>暂时缺货</span>
              )}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">状态</span>
            <span className="detail-value">
              <span className={`badge ${product.status === 'on_sale' ? 'badge-success' : 'badge-gray'}`}>
                {product.status === 'on_sale' ? '在售' : '下架'}
              </span>
            </span>
          </div>

          {/* Quantity selector */}
          <div className="quantity-row" style={{ marginTop: '1.5rem' }}>
            <span className="detail-label">数量</span>
            <div className="qty-control">
              <button onClick={() => setQty(Math.max(1, qty - 1))} disabled={qty <= 1}>−</button>
              <span>{qty}</span>
              <button onClick={() => setQty(Math.min(product.stock, qty + 1))} disabled={qty >= product.stock}>+</button>
            </div>
          </div>

          <button
            className="btn btn-primary btn-lg btn-block"
            onClick={handleAddToCart}
            disabled={adding || product.stock === 0}
            style={{ marginTop: '1.5rem' }}
          >
            {adding ? '添加中...' : product.stock > 0 ? '加入购物车' : '暂时缺货'}
          </button>
        </div>
      </div>
    </div>
  )
}
