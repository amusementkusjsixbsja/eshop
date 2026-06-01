/**
 * API 客户端 — 封装 axios 实例 + 统一拦截器
 * ★ 小A：所有 API 请求都通过此实例发出
 *
 * 使用方式：
 *   client.get('/c-endpoint/products')
 *   client.post('/c-endpoint/auth/login', { email, password })
 *
 * 统一响应拦截：
 *   - code !== 0 → 自动弹窗提示
 *   - 401 → 自动跳转登录页
 */

import axios from 'axios'

const client = axios.create({
  baseURL: '/api/shop',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截 — 自动附加 JWT Token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截 — 统一错误处理
client.interceptors.response.use(
  (response) => {
    const data = response.data
    // 业务错误（code !== 0）
    if (data.code !== 0) {
      console.warn(`[API错误] ${data.message}`, data)
      // 401 → 跳转登录
      if (data.code === 40101) {
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        window.location.href = '/login'
      }
    }
    return data
  },
  (error) => {
    console.error('[网络错误]', error.message)
    return Promise.reject(error)
  }
)

export default client
