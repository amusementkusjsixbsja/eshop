import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../../api/auth'

export default function LoginPage({ onLogin }: { onLogin: (user: any) => void }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
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
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: 20 }}>
      <h1>登录</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div><input placeholder="邮箱" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', padding: 8, margin: '8px 0' }} /></div>
        <div><input type="password" placeholder="密码" value={password} onChange={e => setPassword(e.target.value)} style={{ width: '100%', padding: 8, margin: '8px 0' }} /></div>
        <button type="submit" style={{ width: '100%', padding: 10, background: '#1890ff', color: '#fff', border: 'none', borderRadius: 4 }}>登录</button>
      </form>
      <p style={{ marginTop: 16 }}>还没有账号？<Link to="/register">立即注册</Link></p>
    </div>
  )
}
