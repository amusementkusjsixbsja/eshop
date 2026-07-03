import client from './client'
import type { ApiResponse, PaginatedData, Category, Product, Order } from '../types'

// ─── 分类管理 ───

export async function adminListCategories() {
  return client.get<any, ApiResponse<{ items: Category[] }>>('/b-endpoint/categories')
}

export async function adminCreateCategory(name: string, parent_id?: number | null) {
  return client.post<any, ApiResponse<{ id: number; name: string }>>('/b-endpoint/categories', { name, parent_id })
}

export async function adminUpdateCategory(id: number, name: string, parent_id?: number | null) {
  return client.put<any, ApiResponse<{ id: number; name: string }>>(`/b-endpoint/categories/${id}`, { name, parent_id })
}

export async function adminDeleteCategory(id: number) {
  return client.delete<any, ApiResponse<{ message: string }>>(`/b-endpoint/categories/${id}`)
}

// ─── 商品管理 ───

export async function adminListProducts(params?: { status?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<Product>>>('/b-endpoint/products', { params })
}

export async function adminCreateProduct(data: { name: string; description?: string; price: number; image_url?: string; stock: number; category_id: number }) {
  return client.post<any, ApiResponse<{ id: number }>>('/b-endpoint/products', data)
}

export async function adminUpdateProduct(id: number, data: Partial<{ name: string; description: string; price: number; image_url: string; stock: number; category_id: number }>) {
  return client.put<any, ApiResponse<{ id: number }>>(`/b-endpoint/products/${id}`, data)
}

export async function adminDeleteProduct(id: number) {
  return client.delete<any, ApiResponse<{ message: string }>>(`/b-endpoint/products/${id}`)
}

export async function adminToggleProductStatus(id: number, status: 'on_sale' | 'off_sale') {
  return client.patch<any, ApiResponse<{ id: number; status: string }>>(`/b-endpoint/products/${id}/status`, { status })
}

// ─── 订单查看 ───

export async function adminListOrders(params?: { status?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<Order>>>('/b-endpoint/orders', { params })
}

export async function adminGetOrderDetail(id: number) {
  return client.get<any, ApiResponse<Order>>(`/b-endpoint/orders/${id}`)
}

// ─── 售后管理 ───

export interface AfterSaleItem {
  id: number
  user_id: number
  order_id: number
  type: 'refund' | 'return'
  reason: string
  status: 'pending' | 'approved' | 'rejected' | 'completed'
  created_at: string
  updated_at: string
}

export async function adminListAfterSales(params?: { status?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<AfterSaleItem>>>('/b-endpoint/after-sales', { params })
}

export async function adminApproveAfterSale(id: number) {
  return client.patch<any, ApiResponse<{ id: number; status: string }>>(`/b-endpoint/after-sales/${id}/approve`)
}

export async function adminRejectAfterSale(id: number) {
  return client.patch<any, ApiResponse<{ id: number; status: string }>>(`/b-endpoint/after-sales/${id}/reject`)
}
