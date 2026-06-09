import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../../api/auth'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nickname: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) { setError('密码不能少于 6 位'); return }
    setLoading(true)
    try {
      const res = await register(form.email, form.password, form.nickname)
      if (res.code === 0) {
        navigate('/login')
      } else {
        setError(res.message)
      }
    } catch (err: any) {
      setError(err.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-narrow animate-in">
      <div className="card" style={{ marginTop: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎉</div>
          <h1>创建账号</h1>
          <p className="text-sm text-muted" style={{ marginTop: 4 }}>加入 E-Shop，开启购物之旅</p>
        </div>

        {error && (
          <div style={{
            background: '#FFE4E6', color: '#BE123C', padding: '10px 14px',
            borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">邮箱</label>
            <input className="input" type="email" placeholder="your@email.com"
              value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
          </div>
          <div className="form-group">
            <label className="form-label">密码</label>
            <input className="input" type="password" placeholder="至少 6 位"
              value={form.password} onChange={e => setForm({...form, password: e.target.value})} required />
          </div>
          <div className="form-group">
            <label className="form-label">昵称</label>
            <input className="input" placeholder="您的昵称"
              value={form.nickname} onChange={e => setForm({...form, nickname: e.target.value})} required />
          </div>
          <button type="submit" className="btn btn-primary btn-lg btn-block"
            disabled={loading} style={{ marginTop: '0.5rem' }}>
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <p className="text-sm text-muted text-center" style={{ marginTop: '1.25rem' }}>
          已有账号？ <Link to="/login">去登录</Link>
        </p>
      </div>
    </div>
  )
}
