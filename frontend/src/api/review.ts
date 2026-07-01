import client from './client'
import type { ApiResponse, Review, ReviewStats, PaginatedData } from '../types'

/** 创建商品评价（需已登录且订单已支付） */
export async function createReview(data: {
  product_id: number
  order_id: number
  rating: number
  content: string
}) {
  return client.post<any, ApiResponse<Review>>('/c-endpoint/reviews', data)
}

/** 获取某商品的评价列表（分页） */
export async function getProductReviews(productId: number, page = 1, size = 10) {
  return client.get<any, ApiResponse<PaginatedData<Review>>>(
    `/c-endpoint/reviews/product/${productId}`,
    { params: { page, size } },
  )
}

/** 获取某商品的评价统计 */
export async function getProductReviewStats(productId: number) {
  return client.get<any, ApiResponse<ReviewStats>>(
    `/c-endpoint/reviews/product/${productId}/stats`,
  )
}

/** 获取当前用户自己的评价列表 */
export async function getUserReviews() {
  return client.get<any, ApiResponse<Review[]>>('/c-endpoint/reviews/user/me')
}
