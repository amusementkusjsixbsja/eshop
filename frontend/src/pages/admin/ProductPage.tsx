import { useEffect, useState } from 'react'
import {
  adminListProducts,
  adminCreateProduct,
  adminUpdateProduct,
  adminDeleteProduct,
  adminToggleProductStatus,
  adminListCategories,
} from '../../api/admin'
import type { Product, Category } from '../../types'

interface FormData {
  name: string
  description: string
  price: string
  stock: string
  category_id: number | ''
  image_url: string
}

const emptyForm: FormData = {
  name: '',
  description: '',
  price: '',
  stock: '',
  category_id: '',
  image_url: '',
}

export default function AdminProductPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState<FormData>(emptyForm)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const [prodRes, catRes] = await Promise.all([
        adminListProducts(),
        adminListCategories(),
      ])
      if (prodRes.code === 0) setProducts(prodRes.data.items)
      if (catRes.code === 0) setCategories(catRes.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  // ─── Modal handlers ───

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setShowModal(true)
  }

  const openEdit = (p: Product) => {
    setEditing(p)
    setForm({
      name: p.name,
      description: p.description || '',
      price: String(p.price),
      stock: String(p.stock),
      category_id: p.category_id,
      image_url: p.image_url || '',
    })
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditing(null)
    setForm(emptyForm)
  }

  const handleSubmit = async () => {
    if (!form.name.trim()) { alert('请输入商品名称'); return }
    if (!form.price || Number(form.price) <= 0) { alert('请输入有效价格'); return }
    if (!form.stock || Number(form.stock) < 0) { alert('请输入有效库存'); return }
    if (form.category_id === '') { alert('请选择分类'); return }

    setSubmitting(true)
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        price: Number(form.price),
        stock: Number(form.stock),
        category_id: form.category_id as number,
        image_url: form.image_url.trim(),
      }

      if (editing) {
        await adminUpdateProduct(editing.id, payload)
      } else {
        await adminCreateProduct(payload)
      }
      closeModal()
      load()
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`确定要删除商品「${name}」吗？此操作不可撤销。`)) return
    const res = await adminDeleteProduct(id)
    alert(res.message)
    load()
  }

  const handleToggleStatus = async (id: number, current: string) => {
    const newStatus = current === 'on_sale' ? 'off_sale' : 'on_sale'
    await adminToggleProductStatus(id, newStatus as 'on_sale' | 'off_sale')
    load()
  }

  // ─── Render ───

  return (
    <div className="admin-content animate-in">
        <div className="page-header">
          <h1>商品管理</h1>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="text-sm text-muted">共 {products.length} 件商品</span>
            <button className="btn btn-primary btn-sm" onClick={openCreate}>+ 新增商品</button>
          </div>
        </div>

        {loading ? (
          <div className="state" style={{ minHeight: 300 }}>
            <div className="loading-dots"><span /><span /><span /></div>
          </div>
        ) : products.length === 0 ? (
          <div className="state" style={{ minHeight: 300 }}>
            <div className="state-icon">📦</div>
            <p className="state-title">暂无商品</p>
            <button className="btn btn-primary" onClick={openCreate} style={{ marginTop: 12 }}>发布第一个商品</button>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>名称</th>
                  <th>分类</th>
                  <th>价格</th>
                  <th>库存</th>
                  <th>状态</th>
                  <th style={{ minWidth: 160 }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id}>
                    <td style={{ fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>{p.id}</td>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td><span className="badge badge-gray">{p.category_name || '-'}</span></td>
                    <td className="product-card-price" style={{ fontSize: '1rem' }}>¥{p.price}</td>
                    <td>{p.stock}</td>
                    <td>
                      <span className={`badge ${p.status === 'on_sale' ? 'badge-success' : 'badge-gray'}`}>
                        {p.status === 'on_sale' ? '上架' : '下架'}
                      </span>
                    </td>
                    <td>
                      <div className="btn-group gap-xs">
                        <button className="btn btn-ghost btn-sm" onClick={() => openEdit(p)}>编辑</button>
                        <button
                          className={`btn btn-sm ${p.status === 'on_sale' ? 'btn-outline' : 'btn-primary'}`}
                          onClick={() => handleToggleStatus(p.id, p.status)}
                        >
                          {p.status === 'on_sale' ? '下架' : '上架'}
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id, p.name)}>删除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      {/* ─── Modal ─── */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editing ? '编辑商品' : '新增商品'}</h2>
              <button className="modal-close" onClick={closeModal}>&times;</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">商品名称 <span className="text-danger">*</span></label>
                <input className="input" placeholder="输入商品名称" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">描述</label>
                <textarea className="input" rows={3} placeholder="商品描述（可选）" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">价格 <span className="text-danger">*</span></label>
                  <input className="input" type="number" step="0.01" min="0" placeholder="0.00" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">库存 <span className="text-danger">*</span></label>
                  <input className="input" type="number" min="0" placeholder="0" value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">分类 <span className="text-danger">*</span></label>
                <select className="input" value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value ? Number(e.target.value) : '' }))}>
                  <option value="">— 请选择分类 —</option>
                  {categories.map(c => (
                    <option key={c.id} value={c.id}>{c.parent_id ? `└ ${c.name}` : c.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">图片 URL</label>
                <input className="input" placeholder="https://（可选）" value={form.image_url} onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={closeModal}>取消</button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? '提交中…' : editing ? '保存修改' : '发布商品'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
