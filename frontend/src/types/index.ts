/* ================================================
   TypeScript 类型定义 — 对照接口契约
   ★ 小A：所有接口响应类型在此定义，前端各处复用
   ================================================ */

// ─── 统一响应 ───

export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
  request_id?: string
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// ─── 用户 ───

export interface User {
  id: number
  email: string
  nickname: string
  role: 'user' | 'admin'
  address?: string
}

export interface LoginResponse {
  token: string
  user: User
}

// ─── 商品 ───

export interface Product {
  id: number
  name: string
  description: string
  price: number
  image_url: string
  stock: number
  category_id: number
  category_name?: string
  status: 'on_sale' | 'off_sale'
}

// ─── 分类 ───

export interface Category {
  id: number
  name: string
  parent_id: number | null
  sort_order?: number
  children?: Category[]
}

// ─── 购物车 ───

export interface CartItem {
  id: number
  product_id: number
  name: string
  price: number
  quantity: number
  stock: number
}

// ─── 订单 ───

export type OrderStatus = 'pending' | 'paid' | 'cancelled'

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  price: number
  quantity: number
}

export interface Order {
  id: number
  total_amount: number
  status: OrderStatus
  address: string
  created_at: string
  paid_at?: string
  cancelled_at?: string
  items?: OrderItem[]
}

// ─── 物流 ───

export type LogisticsStatus = 'picked_up' | 'in_transit' | 'out_for_delivery' | 'delivered'

export interface LogisticsNode {
  time: string
  status: string
  location: string
}

export interface Logistics {
  id: number
  order_id: number
  tracking_number: string
  carrier: string
  status: LogisticsStatus
  current_location: string
  estimated_delivery: string
  timeline: LogisticsNode[]
}

// ─── 售后 ───

export type AfterSaleType = 'refund' | 'return' | 'exchange'
export type AfterSaleStatus = 'pending' | 'approved' | 'rejected' | 'completed'

export interface AfterSale {
  id: number
  order_id: number
  type: AfterSaleType
  reason: string
  status: AfterSaleStatus
  created_at: string
}

// ─── AI 对话 ───

export interface ChatRequest {
  question: string
  conversation_id?: string
}

export interface ChatResponse {
  answer: string
  data?: any
}
