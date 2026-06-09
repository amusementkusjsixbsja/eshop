import { useEffect, useState } from 'react'
import { adminListCategories, adminCreateCategory, adminUpdateCategory, adminDeleteCategory } from '../../api/admin'
import type { Category } from '../../types'

export default function AdminCategoryPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [parentId, setParentId] = useState<number | null>(null)
  const [editing, setEditing] = useState<Category | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminListCategories()
      if (res.code === 0) setCategories(res.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (editing) {
      await adminUpdateCategory(editing.id, name, parentId)
    } else {
      await adminCreateCategory(name, parentId)
    }
    setName(''); setParentId(null); setEditing(null)
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个分类吗？')) return
    const res = await adminDeleteCategory(id)
    alert(res.message)
    load()
  }

  return (
    <div className="admin-layout">
      <nav className="admin-sidebar">
        <a href="/admin/categories" className="active">分类管理</a>
        <a href="/admin/products">商品管理</a>
        <a href="/admin/orders">订单管理</a>
      </nav>
      <div className="admin-content animate-in">
        <div className="page-header">
          <h1>分类管理</h1>
        </div>

        {/* Form */}
        <div className="card card-sm" style={{ marginBottom: '1.5rem', maxWidth: 500 }}>
          <h3 style={{ marginBottom: '0.75rem' }}>{editing ? '编辑分类' : '新建分类'}</h3>
          <div className="form-group">
            <label className="form-label">分类名称</label>
            <input className="input" placeholder="输入分类名称" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">父级分类</label>
            <select className="input" value={parentId ?? ''} onChange={e => setParentId(e.target.value ? Number(e.target.value) : null)}>
              <option value="">— 一级分类 —</option>
              {categories.filter(c => !c.parent_id).map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="btn-group">
            <button className="btn btn-primary btn-sm" onClick={handleSubmit}>{editing ? '更新' : '创建'}</button>
            {editing && <button className="btn btn-ghost btn-sm" onClick={() => { setEditing(null); setName(''); setParentId(null) }}>取消</button>}
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="state" style={{ minHeight: 200 }}>
            <div className="loading-dots"><span /><span /><span /></div>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>名称</th>
                  <th>级别</th>
                  <th>排序</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {categories.map(c => {
                  const parent = categories.find(p => p.id === c.parent_id)
                  return (
                    <tr key={c.id}>
                      <td style={{ fontFamily: 'monospace' }}>{c.id}</td>
                      <td style={{ fontWeight: 500 }}>{c.parent_id ? <span style={{ marginLeft: 16 }}>└ {c.name}</span> : c.name}</td>
                      <td><span className="badge badge-gray">{c.parent_id ? '二级' : '一级'}</span></td>
                      <td>{c.sort_order ?? '-'}</td>
                      <td>
                        <div className="btn-group gap-xs">
                          <button className="btn btn-ghost btn-sm" onClick={() => { setEditing(c); setName(c.name); setParentId(c.parent_id) }}>编辑</button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(c.id)}>删除</button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
