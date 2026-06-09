import client from './client'
import type { ApiResponse } from '../types'

export interface Address {
  id: number
  user_id: number
  label: string
  name: string
  phone: string
  address: string
  is_default: boolean
  created_at: string
}

export async function listAddresses() {
  return client.get<any, ApiResponse<{ items: Address[] }>>('/c-endpoint/addresses')
}

export async function createAddress(data: { label?: string; name: string; phone: string; address: string; is_default?: boolean }) {
  return client.post<any, ApiResponse<{ id: number }>>('/c-endpoint/addresses', data)
}

export async function updateAddress(id: number, data: Partial<{ label: string; name: string; phone: string; address: string; is_default: boolean }>) {
  return client.put<any, ApiResponse<{ id: number }>>(`/c-endpoint/addresses/${id}`, data)
}

export async function deleteAddress(id: number) {
  return client.delete<any, ApiResponse<{ message: string }>>(`/c-endpoint/addresses/${id}`)
}

export async function setDefaultAddress(id: number) {
  return client.patch<any, ApiResponse<{ id: number; is_default: boolean }>>(`/c-endpoint/addresses/${id}/default`)
}
