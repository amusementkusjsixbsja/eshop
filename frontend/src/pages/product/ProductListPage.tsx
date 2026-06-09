import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { listProducts, getCategoryTree, getHotProducts } from '../../api/product'
import type { Product, Category } from '../../types'

export default function ProductListPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [hotProducts, setHotProducts] = useState<Product[]>([])
  const [keyword, setKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)

  const loadProducts = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listProducts({ category_id: selectedCategory, keyword: keyword || undefined })
      if (res.code === 0) setProducts(res.data.items)
    } finally {
      setLoading(false)
    }
  }, [selectedCategory, keyword])

  useEffect(() => {
    getCategoryTree().then(res => res.code === 0 && setCategories(res.data.items || []))
    getHotProducts().then(res => res.code === 0 && setHotProducts(res.data.items || []))
  }, [])

  useEffect(() => {
    loadProducts()
  }, [loadProducts])

  return (
    <div className="page animate-in">
      {/* Header */}
      <div className="page-header">
        <h1>全部商品</h1>
      </div>

      {/* Search */}
      <div className="input-group" style={{ marginBottom: '1rem', maxWidth: 400 }}>
        <input
          className="input"
          placeholder="搜索商品..."
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && loadProducts()}
        />
        <button className="btn btn-primary" onClick={loadProducts}>搜索</button>
      </div>

      {/* Categories */}
      <div className="category-bar">
        <button
          className={`category-btn${!selectedCategory ? ' active' : ''}`}
          onClick={() => { setSelectedCategory(undefined) }}
        >全部</button>
        {categories.map(c => (
          <button
            key={c.id}
            className={`category-btn${selectedCategory === c.id ? ' active' : ''}`}
            onClick={() => setSelectedCategory(c.id)}
          >{c.name}</button>
        ))}
      </div>

      {/* Hot Products Banner */}
      {hotProducts.length > 0 && (
        <div className="hot-banner animate-in animate-in-d1">
          <div className="hot-banner-title">
            <span>🔥</span> 热门推荐
          </div>
          <div className="hot-scroll">
            {hotProducts.map(p => (
              <Link key={p.id} to={`/products/${p.id}`} className="hot-chip">
                {p.name} — ¥{p.price}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Product Grid */}
      {loading ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
          <p className="state-desc" style={{ marginTop: '1rem' }}>加载商品中...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">📦</div>
          <p className="state-title">暂无商品</p>
          <p className="state-desc">当前分类下还没有上架商品，试试其他分类吧</p>
        </div>
      ) : (
        <div className="product-grid">
          {products.map((p, i) => (
            <Link key={p.id} to={`/products/${p.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="product-card animate-in" style={{ animationDelay: `${i * 0.04}s` }}>
                <img
                  src={p.image_url}
                  alt={p.name}
                  className="product-card-img"
                  loading="lazy"
                  onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x400?text=' + p.name }}
                />
                <div className="product-card-body">
                  <h3 className="product-card-name">{p.name}</h3>
                  <p className="product-card-desc">{p.description}</p>
                </div>
                <div className="product-card-footer">
                  <span className="product-card-price">¥{p.price}</span>
                  <span className="product-card-stock">库存 {p.stock}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
