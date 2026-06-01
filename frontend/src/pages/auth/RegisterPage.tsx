import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../../api/auth'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nickname: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) { setError('密码不能少于 6 位'); return }
    try {
      const res = await register(form.email, form.password, form.nickname)
      if (res.code === 0) {
        navigate('/login')
      } else {
        setError(res.message)
      }
    } catch (err: any) {
      setError(err.message || '注册失败')
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: 20 }}>
      <h1>注册</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input placeholder="邮箱" value={form.email} onChange={e => setForm({...form, email: e.target.value})} style={{ width: '100%', padding: 8, margin: '8px 0' }} />
        <input type="password" placeholder="密码（至少6位）" value={form.password} onChange={e => setForm({...form, password: e.target.value})} style={{ width: '100%', padding: 8, margin: '8px 0' }} />
        <input placeholder="昵称" value={form.nickname} onChange={e => setForm({...form, nickname: e.target.value})} style={{ width: '100%', padding: 8, margin: '8px 0' }} />
        <button type="submit" style={{ width: '100%', padding: 10, background: '#52c41a', color: '#fff', border: 'none', borderRadius: 4 }}>注册</button>
      </form>
      <p style={{ marginTop: 16 }}>已有账号？<Link to="/login">去登录</Link></p>
    </div>
  )
}
