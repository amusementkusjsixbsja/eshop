import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import ChatPopup from './components/ChatPopup'

// 页面导入（★ 小A：替换为实际页面组件）
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ProductListPage from './pages/product/ProductListPage'
import ProductDetailPage from './pages/product/ProductDetailPage'
import CartPage from './pages/cart/CartPage'
import OrderListPage from './pages/order/OrderListPage'
import OrderDetailPage from './pages/order/OrderDetailPage'
import LogisticsPage from './pages/logistics/LogisticsPage'
import AfterSalePage from './pages/afterSale/AfterSalePage'
import AdminCategoryPage from './pages/admin/CategoryPage'
import AdminProductPage from './pages/admin/ProductPage'
import AdminOrderPage from './pages/admin/OrderPage'

function App() {
  const [user, setUser] = useState<{ id: number; email: string; role: string } | null>(null)

  return (
    <BrowserRouter>
      <Routes>
        {/* 公共页面 */}
        <Route path="/login" element={<LoginPage onLogin={setUser} />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* 商品浏览（无需登录） */}
        <Route path="/products" element={<ProductListPage />} />
        <Route path="/products/:id" element={<ProductDetailPage />} />

        {/* C端 - 需登录 */}
        <Route path="/cart" element={<RequireAuth><CartPage /></RequireAuth>} />
        <Route path="/orders" element={<RequireAuth><OrderListPage /></RequireAuth>} />
        <Route path="/orders/:id" element={<RequireAuth><OrderDetailPage /></RequireAuth>} />
        <Route path="/logistics/:orderId" element={<RequireAuth><LogisticsPage /></RequireAuth>} />
        <Route path="/after-sales" element={<RequireAuth><AfterSalePage /></RequireAuth>} />

        {/* B端 - 需管理员 */}
        <Route path="/admin/categories" element={<RequireAdmin><AdminCategoryPage /></RequireAdmin>} />
        <Route path="/admin/products" element={<RequireAdmin><AdminProductPage /></RequireAdmin>} />
        <Route path="/admin/orders" element={<RequireAdmin><AdminOrderPage /></RequireAdmin>} />

        {/* 默认跳转 */}
        <Route path="/" element={<Navigate to="/products" replace />} />
        <Route path="*" element={<Navigate to="/products" replace />} />
      </Routes>

      {/* AI 客服浮窗 */}
      <ChatPopup user={user} />
    </BrowserRouter>
  )
}

// ─── 路由守卫组件 ───

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  if (role !== 'admin') {
    return <Navigate to="/products" replace />
  }
  return <>{children}</>
}

export default App
