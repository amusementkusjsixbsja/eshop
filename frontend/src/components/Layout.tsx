import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
  user?: { id: number; email: string; role: string } | null
  onLogout?: () => void
}

export default function Layout({ children, user, onLogout }: LayoutProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  // Check if we're on an admin page
  const isAdmin = location.pathname.startsWith('/admin')
  const isLoggedIn = !!localStorage.getItem('token')
  const role = localStorage.getItem('role')

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    onLogout?.()
    navigate('/products')
  }

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/')

  const navLinks = isAdmin ? (
    <>
      <Link to="/admin/categories" className={isActive('/admin/categories') ? 'active' : ''} onClick={() => setMenuOpen(false)}>分类管理</Link>
      <Link to="/admin/products" className={isActive('/admin/products') ? 'active' : ''} onClick={() => setMenuOpen(false)}>商品管理</Link>
      <Link to="/admin/orders" className={isActive('/admin/orders') ? 'active' : ''} onClick={() => setMenuOpen(false)}>订单管理</Link>
      <Link to="/admin/after-sales" className={isActive('/admin/after-sales') ? 'active' : ''} onClick={() => setMenuOpen(false)}>售后管理</Link>
    </>
  ) : (
    <>
      <Link to="/products" className={isActive('/products') ? 'active' : ''} onClick={() => setMenuOpen(false)}>商品</Link>
      {isLoggedIn && (
        <>
          <Link to="/cart" className={isActive('/cart') ? 'active' : ''} onClick={() => setMenuOpen(false)}>购物车</Link>
          <Link to="/orders" className={isActive('/orders') ? 'active' : ''} onClick={() => setMenuOpen(false)}>订单</Link>
          <Link to="/addresses" className={isActive('/addresses') ? 'active' : ''} onClick={() => setMenuOpen(false)}>地址</Link>
          <Link to="/after-sales" className={isActive('/after-sales') ? 'active' : ''} onClick={() => setMenuOpen(false)}>售后</Link>
          {role === 'admin' && (
            <>
              <div className="nav-divider" />
              <Link to="/admin/categories" onClick={() => setMenuOpen(false)}>管理后台</Link>
            </>
          )}
        </>
      )}
    </>
  )

  return (
    <>
      <header className="header">
        <div className="header-inner">
          <Link to="/products" className="header-logo">
            <span className="header-logo-icon">E</span>
            E-Shop
          </Link>

          <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="菜单">
            <span /><span /><span />
          </button>

          <nav className={`header-nav${menuOpen ? ' open' : ''}`}>
            {navLinks}
            <div className="nav-divider" />
            {isLoggedIn ? (
              <>
                <span className="user-badge">{user?.email?.split('@')[0] || '用户'}</span>
                <button onClick={handleLogout}>退出</button>
              </>
            ) : (
              <>
                <Link to="/login" onClick={() => setMenuOpen(false)}>登录</Link>
                <Link to="/register" className="btn btn-sm btn-primary" onClick={() => setMenuOpen(false)}>注册</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main>
        {children}
      </main>
    </>
  )
}
