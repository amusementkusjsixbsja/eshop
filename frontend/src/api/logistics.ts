import client from './client'
import type { ApiResponse, Logistics } from '../types'

export async function getLogistics(order_id: number) {
  return client.get<any, ApiResponse<Logistics>>(`/c-endpoint/logistics/${order_id}`)
}
