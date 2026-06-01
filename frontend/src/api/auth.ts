import client from './client'
import type { ApiResponse, LoginResponse, User } from '../types'

export async function register(email: string, password: string, nickname: string) {
  return client.post<any, ApiResponse<{ id: number }>>('/c-endpoint/auth/register', {
    email, password, nickname,
  })
}

export async function login(email: string, password: string) {
  return client.post<any, ApiResponse<LoginResponse>>('/c-endpoint/auth/login', {
    email, password,
  })
}

export async function getProfile() {
  return client.get<any, ApiResponse<User>>('/c-endpoint/auth/me')
}

export async function updateAddress(address: string) {
  return client.put<any, ApiResponse<{ id: number; address: string }>>('/c-endpoint/auth/address', {
    address,
  })
}
