import { useEffect, useState } from 'react'
import { adminListProducts, adminCreateProduct, adminUpdateProduct, adminToggleProductStatus } from '../../api/admin'
import type { Product } from '../../types'

export default function AdminProductPage() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => { load() }, [])

  const load = async () => {
    const res = await adminListProducts()
    if (res.code === 0) setProducts(res.data.items)
  }

  const handleToggleStatus = async (id: number, current: string) => {
    const newStatus = current === 'on_sale' ? 'off_sale' : 'on_sale'
    await adminToggleProductStatus(id, newStatus)
    load()
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      <h1>商品管理</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr><th>ID</th><th>名称</th><th>价格</th><th>库存</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id}>
              <td>{p.id}</td><td>{p.name}</td><td>¥{p.price}</td><td>{p.stock}</td>
              <td>{p.status === 'on_sale' ? '上架' : '下架'}</td>
              <td><button onClick={() => handleToggleStatus(p.id, p.status)}>{p.status === 'on_sale' ? '下架' : '上架'}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
