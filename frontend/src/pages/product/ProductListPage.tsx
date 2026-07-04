import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { listProducts, getCategoryTree, getHotProducts } from '../../api/product'
import ProductImage from '../../components/ProductImage'
import type { Product, Category } from '../../types'

export default function ProductListPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [hotProducts, setHotProducts] = useState<Product[]>([])
  const [keyword, setKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>()
  const [selectedParent, setSelectedParent] = useState<number | undefined>()
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

  // 选中一级分类：显示该分类下商品 + 展开其子分类
  const selectParent = (c: Category) => {
    setSelectedParent(c.id)
    setSelectedCategory(c.id)
  }
  // 选中「全部」
  const selectAll = () => {
    setSelectedParent(undefined)
    setSelectedCategory(undefined)
  }
  // 当前展开的一级分类的子分类
  const childCategories = categories.find(c => c.id === selectedParent)?.children || []

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

      {/* Categories — 一级分类 */}
      <div className="category-bar">
        <button
          className={`category-btn${!selectedParent ? ' active' : ''}`}
          onClick={selectAll}
        >全部</button>
        {categories.map(c => (
          <button
            key={c.id}
            className={`category-btn${selectedParent === c.id ? ' active' : ''}`}
            onClick={() => selectParent(c)}
          >{c.name}</button>
        ))}
      </div>

      {/* Categories — 二级分类（选中一级后显示） */}
      {childCategories.length > 0 && (
        <div className="category-bar" style={{ marginTop: -8, paddingLeft: 8 }}>
          <button
            className={`category-btn${selectedCategory === selectedParent ? ' active' : ''}`}
            onClick={() => setSelectedCategory(selectedParent)}
          >全部{categories.find(c => c.id === selectedParent)?.name}</button>
          {childCategories.map(sc => (
            <button
              key={sc.id}
              className={`category-btn${selectedCategory === sc.id ? ' active' : ''}`}
              onClick={() => setSelectedCategory(sc.id)}
            >{sc.name}</button>
          ))}
        </div>
      )}

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
                <ProductImage
                  name={p.name}
                  categoryId={p.category_id}
                  className="product-card-img"
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
