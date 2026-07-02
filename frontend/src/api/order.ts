import client from './client'
import type { ApiResponse, PaginatedData, Order, PaymentRecord } from '../types'

export async function createOrder(address: string) {
  return client.post<any, ApiResponse<Order>>('/c-endpoint/orders', { address })
}

export async function listOrders(params?: { status?: string; page?: number; size?: number }) {
  return client.get<any, ApiResponse<PaginatedData<Order>>>('/c-endpoint/orders', { params })
}

export async function getOrderDetail(id: number) {
  return client.get<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}`)
}

export async function payOrder(id: number, paymentMethod?: string) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/pay`, {
    payment_method: paymentMethod || 'mock',
  })
}

/** 查询支付状态（供前端轮询支付结果） */
export async function getPaymentStatus(id: number) {
  return client.get<any, ApiResponse<PaymentRecord>>(`/c-endpoint/orders/${id}/payment`)
}

export async function cancelOrder(id: number) {
  return client.post<any, ApiResponse<Order>>(`/c-endpoint/orders/${id}/cancel`)
}
