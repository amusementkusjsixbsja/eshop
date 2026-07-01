import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProductDetail } from '../../api/product'
import { addToCart } from '../../api/cart'
import { getProductReviews, getProductReviewStats } from '../../api/review'
import StarRating from '../../components/StarRating'
import type { Product, Review, ReviewStats } from '../../types'

const REVIEW_PAGE_SIZE = 10

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [qty, setQty] = useState(1)
  const [adding, setAdding] = useState(false)

  // ── 评价（v2.0） ──
  const [activeTab, setActiveTab] = useState<'details' | 'reviews'>('details')
  const [reviews, setReviews] = useState<Review[]>([])
  const [reviewStats, setReviewStats] = useState<ReviewStats | null>(null)
  const [reviewPage, setReviewPage] = useState(1)
  const [reviewTotal, setReviewTotal] = useState(0)

  useEffect(() => {
    if (id) {
      setLoading(true)
      getProductDetail(Number(id)).then(res => {
        if (res.code === 0) setProduct(res.data)
        setLoading(false)
      })
    }
  }, [id])

  useEffect(() => {
    if (!id) return
    getProductReviews(Number(id), reviewPage, REVIEW_PAGE_SIZE).then(r => {
      if (r.code === 0) {
        setReviews(r.data.items || [])
        setReviewTotal(r.data.total || 0)
      }
    })
  }, [id, reviewPage])

  useEffect(() => {
    if (!id) return
    getProductReviewStats(Number(id)).then(r => {
      if (r.code === 0) setReviewStats(r.data)
    })
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

      {/* Tabs: 详情 / 评价 */}
      <div style={{ marginTop: '2rem', display: 'flex', gap: '8px', borderBottom: '1px solid var(--color-border)' }}>
        <button
          className={`btn btn-ghost btn-sm ${activeTab === 'details' ? 'font-semibold' : ''}`}
          onClick={() => setActiveTab('details')}
          style={{ borderBottom: activeTab === 'details' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent', borderRadius: 0 }}
        >
          商品详情
        </button>
        <button
          className={`btn btn-ghost btn-sm ${activeTab === 'reviews' ? 'font-semibold' : ''}`}
          onClick={() => setActiveTab('reviews')}
          style={{ borderBottom: activeTab === 'reviews' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent', borderRadius: 0 }}
        >
          商品评价{reviewStats ? ` (${reviewStats.total_count})` : ''}
        </button>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        {activeTab === 'details' ? (
          <p style={{ whiteSpace: 'pre-wrap', color: 'var(--color-text, #374151)' }}>{product.description || '暂无详情'}</p>
        ) : (
          <div>
            {reviewStats && reviewStats.total_count > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center', minWidth: 80 }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold' }}>{reviewStats.avg_rating.toFixed(1)}</div>
                  <StarRating rating={Math.round(reviewStats.avg_rating)} size="sm" />
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: 4 }}>{reviewStats.total_count} 条评价</div>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  {[5, 4, 3, 2, 1].map(star => (
                    <div key={star} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', width: '28px' }}>{star} 星</span>
                      <div style={{ flex: 1, height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${reviewStats.total_count > 0 ? ((reviewStats.distribution[star] || 0) / reviewStats.total_count) * 100 : 0}%`,
                          backgroundColor: '#f59e0b',
                          borderRadius: '4px',
                        }} />
                      </div>
                      <span style={{ fontSize: '12px', color: '#6b7280', width: '28px', textAlign: 'right' }}>
                        {reviewStats.distribution[star] || 0}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {reviews.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>暂无评价</div>
            ) : (
              reviews.map(review => (
                <div key={review.id} style={{ padding: '12px 0', borderBottom: '1px solid #e5e7eb' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <StarRating rating={review.rating} size="sm" />
                    <span style={{ fontSize: '14px', color: '#374151' }}>{review.nickname || '匿名用户'}</span>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>{review.created_at?.slice(0, 10)}</span>
                  </div>
                  {review.content && <div style={{ fontSize: '14px', color: '#4b5563' }}>{review.content}</div>}
                </div>
              ))
            )}

            {reviewTotal > REVIEW_PAGE_SIZE && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '16px' }}>
                <button className="btn btn-outline btn-sm" disabled={reviewPage <= 1} onClick={() => setReviewPage(p => Math.max(1, p - 1))}>
                  上一页
                </button>
                <span style={{ fontSize: '13px', color: '#6b7280', alignSelf: 'center' }}>
                  {reviewPage} / {Math.ceil(reviewTotal / REVIEW_PAGE_SIZE)}
                </span>
                <button className="btn btn-outline btn-sm" disabled={reviewPage >= Math.ceil(reviewTotal / REVIEW_PAGE_SIZE)} onClick={() => setReviewPage(p => p + 1)}>
                  下一页
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
