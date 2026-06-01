import client from './client'
import type { ApiResponse, PaginatedData, Order } from '../types'

export async function createOrder(address: string) {
  return client.post<any, ApiResponse<Order>>('/c-endpoint/orders', { address })
}

export async function listOrders(params?: { status?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<Order>>>('/c-endpoint/orders', { params })
}

export async function getOrderDetail(id: number) {
  return client.get<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}`)
}

export async function payOrder(id: number) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/pay`)
}

export async function cancelOrder(id: number) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/cancel`)
}
