import client from './client'
import type { ApiResponse, PaginatedData, Product, Category } from '../types'

export async function listProducts(params?: { category_id?: number; keyword?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<Product>>>('/c-endpoint/products', { params })
}

export async function getHotProducts() {
  return client.get<any, ApiResponse<{ items: Product[] }>>('/c-endpoint/products/hot')
}

export async function getProductDetail(id: number) {
  return client.get<any, ApiResponse<Product>>(`/c-endpoint/products/${id}`)
}

export async function getCategoryTree() {
  return client.get<any, ApiResponse<{ items: Category[] }>>('/c-endpoint/products/categories/tree')
}
