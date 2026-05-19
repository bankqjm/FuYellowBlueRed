
import api from './api'
import { PageResponse } from './shop'

export interface CouponInfo {
  id: number
  code: string
  name: string
  description?: string
  discount_amount: number
  min_order_amount: number
  total_count: number
  remain_count: number
  valid_from: string
  valid_until: string
  status: string
  is_claimed: boolean
}

export interface UserCouponInfo {
  id: number
  coupon_id: number
  status: string
  claimed_at: string
  used_at?: string
  coupon: CouponInfo
}

export const couponsApi = {
  listAvailableCoupons: (params?: { page?: number; page_size?: number }) =>
    api.get<PageResponse<CouponInfo>>('/coupons', { params }),

  claimCoupon: (couponId: number) =>
    api.post<UserCouponInfo>(`/coupons/${couponId}/claim`),

  listMyCoupons: (params?: { status?: string; page?: number; page_size?: number }) =>
    api.get<PageResponse<UserCouponInfo>>('/coupons/my', { params }),

  applyCoupon: (couponId: number, orderAmount: number) =>
    api.post<{ coupon_id: number; discount_amount: number; final_amount: number }>(
      '/coupons/apply',
      { coupon_id: couponId, order_amount: orderAmount }
    ),
}
