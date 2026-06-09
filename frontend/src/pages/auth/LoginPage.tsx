import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../../api/auth'

export default function LoginPage({ onLogin }: { onLogin: (user: any) => void }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await login(email, password)
      if (res.code === 0) {
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('role', res.data.user.role)
        onLogin(res.data.user)
        navigate(res.data.user.role === 'admin' ? '/admin/products' : '/products')
      } else {
        setError(res.message)
      }
    } catch (err: any) {
      setError(err.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-narrow animate-in">
      <div className="card" style={{ marginTop: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👋</div>
          <h1>欢迎回来</h1>
          <p className="text-sm text-muted" style={{ marginTop: 4 }}>登录您的 E-Shop 账号</p>
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
            <input
              className="input"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">密码</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary btn-lg btn-block"
            disabled={loading}
            style={{ marginTop: '0.5rem' }}
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="text-sm text-muted text-center" style={{ marginTop: '1.25rem' }}>
          还没有账号？ <Link to="/register">立即注册</Link>
        </p>
      </div>
    </div>
  )
}
