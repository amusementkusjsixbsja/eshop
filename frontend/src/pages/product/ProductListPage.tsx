import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listProducts, getCategoryTree, getHotProducts } from '../../api/product'
import type { Product, Category } from '../../types'

export default function ProductListPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [hotProducts, setHotProducts] = useState<Product[]>([])
  const [keyword, setKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>()

  useEffect(() => {
    getCategoryTree().then(res => res.code === 0 && setCategories(res.data.items || []))
    getHotProducts().then(res => res.code === 0 && setHotProducts(res.data.items || []))
    loadProducts()
  }, [])

  const loadProducts = async () => {
    const res = await listProducts({ category_id: selectedCategory, keyword: keyword || undefined })
    if (res.code === 0) setProducts(res.data.items)
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      <h1>商品列表 <Link to="/login">登录</Link> | <Link to="/cart">购物车</Link> | <Link to="/orders">我的订单</Link></h1>

      {/* 搜索 */}
      <div style={{ margin: '16px 0', display: 'flex', gap: 8 }}>
        <input placeholder="搜索商品" value={keyword} onChange={e => setKeyword(e.target.value)} style={{ flex: 1, padding: 8 }} />
        <button onClick={loadProducts} style={{ padding: '8px 16px' }}>搜索</button>
      </div>

      {/* 分类 */}
      <div style={{ margin: '8px 0', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={() => { setSelectedCategory(undefined); loadProducts() }}>全部</button>
        {categories.map(c => <button key={c.id} onClick={() => { setSelectedCategory(c.id); loadProducts() }}>{c.name}</button>)}
      </div>

      {/* 热门推荐 */}
      {hotProducts.length > 0 && (
        <div style={{ margin: '16px 0', padding: 16, background: '#fff7e6', borderRadius: 8 }}>
          <h3>🔥 热门推荐</h3>
          <div style={{ display: 'flex', gap: 16 }}>
            {hotProducts.map(p => (
              <Link key={p.id} to={`/products/${p.id}`} style={{ textDecoration: 'none' }}>
                <div style={{ padding: 8 }}>{p.name} - ¥{p.price}</div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* 商品列表 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
        {products.map(p => (
          <Link key={p.id} to={`/products/${p.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div style={{ border: '1px solid #eee', borderRadius: 8, padding: 16 }}>
              <img src={p.image_url} alt={p.name} style={{ width: '100%', height: 150, objectFit: 'cover', borderRadius: 4 }} />
              <h3>{p.name}</h3>
              <p style={{ color: '#f5222d', fontSize: 18 }}>¥{p.price}</p>
              <p style={{ color: '#999' }}>库存 {p.stock}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
