import { useEffect, useState } from 'react'
import { adminListCategories, adminCreateCategory, adminUpdateCategory, adminDeleteCategory } from '../../api/admin'
import type { Category } from '../../types'

export default function AdminCategoryPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [parentId, setParentId] = useState<number | null>(null)
  const [editing, setEditing] = useState<Category | null>(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    const res = await adminListCategories()
    if (res.code === 0) setCategories(res.data.items || [])
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
    if (!confirm('确定删除？')) return
    const res = await adminDeleteCategory(id)
    alert(res.message); load()
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <h1>分类管理</h1>
      <div style={{ border: '1px solid #eee', borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <h3>{editing ? '编辑分类' : '新建分类'}</h3>
        <input placeholder="分类名称" value={name} onChange={e => setName(e.target.value)} style={{ width: '100%', padding: 8, margin: '4px 0' }} />
        <select value={parentId ?? ''} onChange={e => setParentId(e.target.value ? Number(e.target.value) : null)} style={{ width: '100%', padding: 8, margin: '4px 0' }}>
          <option value="">一级分类</option>
          {categories.filter(c => !c.parent_id).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleSubmit} style={{ padding: '8px 24px', background: '#1890ff', color: '#fff', border: 'none', borderRadius: 4 }}>{editing ? '更新' : '创建'}</button>
          {editing && <button onClick={() => { setEditing(null); setName(''); setParentId(null) }}>取消</button>}
        </div>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr><th>ID</th><th>名称</th><th>父级</th><th>操作</th></tr></thead>
        <tbody>
          {categories.map(c => (
            <tr key={c.id}><td>{c.id}</td><td>{c.name}</td><td>{c.parent_id || '-'}</td>
              <td><button onClick={() => { setEditing(c); setName(c.name); setParentId(c.parent_id) }}>编辑</button>
              <button onClick={() => handleDelete(c.id)} style={{ color: 'red', marginLeft: 8 }}>删除</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
