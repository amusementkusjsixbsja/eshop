import { useEffect, useState } from 'react'
import { listAddresses, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../api/address'
import type { Address } from '../../api/address'

const emptyForm = { label: '', name: '', phone: '', address: '', is_default: false }

export default function AddressPage() {
  const [addresses, setAddresses] = useState<Address[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Address | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await listAddresses()
      if (res.code === 0) setAddresses(res.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setForm(emptyForm)
    setEditing(null)
    setShowForm(true)
  }

  const openEdit = (a: Address) => {
    setForm({ label: a.label, name: a.name, phone: a.phone, address: a.address, is_default: a.is_default })
    setEditing(a)
    setShowForm(true)
  }

  const handleSubmit = async () => {
    if (!form.name.trim() || !form.phone.trim() || !form.address.trim()) {
      alert('请填写完整信息'); return
    }
    setSaving(true)
    try {
      if (editing) {
        await updateAddress(editing.id, form)
      } else {
        await createAddress(form)
      }
      setShowForm(false)
      setEditing(null)
      load()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个地址吗？')) return
    await deleteAddress(id)
    load()
  }

  const handleSetDefault = async (id: number) => {
    await setDefaultAddress(id)
    load()
  }

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>📍 地址管理</h1>
        {!showForm && <button className="btn btn-primary btn-sm" onClick={openCreate}>+ 新增地址</button>}
      </div>

      {/* Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '1.5rem', maxWidth: 500 }}>
          <h3 style={{ marginBottom: '0.75rem' }}>{editing ? '编辑地址' : '新增地址'}</h3>
          <div className="form-group">
            <label className="form-label">标签（可选）</label>
            <input className="input" placeholder="如：家、公司" value={form.label} onChange={e => setForm({...form, label: e.target.value})} />
          </div>
          <div className="flex gap-sm">
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">收货人</label>
              <input className="input" placeholder="姓名" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">手机号</label>
              <input className="input" placeholder="手机号" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">详细地址</label>
            <textarea className="input" placeholder="省市区/街道/门牌号" value={form.address} onChange={e => setForm({...form, address: e.target.value})} rows={2} />
          </div>
          <div className="form-group flex items-center gap-sm">
            <input type="checkbox" id="isDefault" checked={form.is_default}
              onChange={e => setForm({...form, is_default: e.target.checked})} />
            <label htmlFor="isDefault" style={{ fontSize: '0.9rem' }}>设为默认地址</label>
          </div>
          <div className="btn-group">
            <button className="btn btn-primary btn-sm" onClick={handleSubmit} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => { setShowForm(false); setEditing(null) }}>取消</button>
          </div>
        </div>
      )}

      {/* Address List */}
      {loading ? (
        <div className="state" style={{ minHeight: 200 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : addresses.length === 0 && !showForm ? (
        <div className="state" style={{ minHeight: 200 }}>
          <div className="state-icon">📍</div>
          <p className="state-title">暂无地址</p>
          <p className="state-desc">添加一个收货地址，方便下单时选择</p>
          <button className="btn btn-primary" onClick={openCreate}>+ 新增地址</button>
        </div>
      ) : (
        <div>
          {addresses.map((a, i) => (
            <div key={a.id} className="card card-hover animate-in" style={{ animationDelay: `${i * 0.05}s`, marginBottom: '0.75rem' }}>
              <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
                <div className="flex items-center gap-sm">
                  <span style={{ fontWeight: 600 }}>{a.name}</span>
                  {a.label && <span className="badge badge-primary">{a.label}</span>}
                  {a.is_default && <span className="badge badge-success">默认</span>}
                </div>
                <div className="btn-group gap-xs">
                  {!a.is_default && (
                    <button className="btn btn-ghost btn-sm" onClick={() => handleSetDefault(a.id)}>设为默认</button>
                  )}
                  <button className="btn btn-ghost btn-sm" onClick={() => openEdit(a)}>编辑</button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(a.id)}>删除</button>
                </div>
              </div>
              <div className="text-sm">
                <span style={{ color: 'var(--gray-600)' }}>{a.phone}</span>
              </div>
              <div className="text-sm text-muted" style={{ marginTop: 2 }}>{a.address}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
