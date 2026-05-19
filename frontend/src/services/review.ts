
import api from './api'
import { PageResponse } from './shop'

export interface ReviewInfo {
  id: number
  order_id: number
  user_id: number
  shop_id: number
  rider_id?: number
  shop_rating: number
  rider_rating?: number
  content?: string
  images?: string[]
  created_at?: string
  user_nickname?: string
}

export const reviewApi = {
  createReview: (data: {
    order_id: number
    shop_rating: number
    rider_rating?: number
    content?: string
    images?: string[]
  }) => api.post<ReviewInfo>('/reviews', data),

  getShopReviews: (shopId: number, params?: {
    page?: number
    page_size?: number
  }) => api.get<PageResponse<ReviewInfo>>(`/reviews/shop/${shopId}`, { params }),

  getOrderReview: (orderId: number) => api.get<ReviewInfo>(`/reviews/order/${orderId}`),
}

