import client from './client'
import type { ApiResponse, AfterSale } from '../types'

export async function createAfterSale(order_id: number, type: string, reason: string = '') {
  return client.post<any, ApiResponse<{ id: number; status: string }>>('/c-endpoint/after-sales', {
    order_id, type, reason,
  })
}

export async function listAfterSales() {
  return client.get<any, ApiResponse<{ items: AfterSale[] }>>('/c-endpoint/after-sales')
}
