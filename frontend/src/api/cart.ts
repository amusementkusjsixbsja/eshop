import client from './client'
import type { ApiResponse, CartItem } from '../types'

export async function getCart() {
  return client.get<any, ApiResponse<{ items: CartItem[] }>>('/c-endpoint/cart')
}

export async function addToCart(product_id: number, quantity: number = 1) {
  return client.post<any, ApiResponse<{ id: number; product_id: number; quantity: number }>>('/c-endpoint/cart', {
    product_id, quantity,
  })
}

export async function updateCartItem(product_id: number, quantity: number) {
  return client.put<any, ApiResponse<{ product_id: number; quantity: number }>>(`/c-endpoint/cart/${product_id}`, {
    quantity,
  })
}

export async function deleteCartItem(product_id: number) {
  return client.delete<any, ApiResponse<{ message: string }>>(`/c-endpoint/cart/${product_id}`)
}
