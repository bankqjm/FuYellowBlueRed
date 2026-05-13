
import api from './api'
import { OrderInfo, PageResponse } from './shop'

export interface EarningsInfo {
  id: number
  order_id: number
  amount: number
  type: string
  created_at?: string
}

export interface EarningsSummary {
  total_earnings: number
  balance: number
}

export interface WithdrawalRecord {
  id: number
  amount: number
  method: string
  account: string
  status: string
  created_at?: string
}

export const riderApi = {
  getAvailableOrders: (params?: {
    page?: number
    page_size?: number
  }) => api.get<PageResponse<OrderInfo>>('/rider/orders/available', { params }),

  getActiveOrders: (params?: {
    page?: number
    page_size?: number
  }) => api.get<PageResponse<OrderInfo>>('/rider/orders/active', { params }),

  acceptOrder: (orderId: number) => api.put<OrderInfo>(`/rider/orders/${orderId}/accept`),

  deliverOrder: (orderId: number) => api.put<OrderInfo>(`/rider/orders/${orderId}/deliver`),

  getEarnings: (params?: {
    page?: number
    page_size?: number
  }) => api.get<PageResponse<EarningsInfo>>('/rider/earnings', { params }),

  getEarningsSummary: () => api.get<EarningsSummary>('/rider/earnings/summary'),

  withdraw: (amount: number) => api.post<{ withdraw_id: number; amount: number }>('/rider/withdraw', { amount }),

  getWithdrawalRecords: (params?: {
    page?: number
    page_size?: number
  }) => api.get<PageResponse<WithdrawalRecord>>('/rider/withdrawals', { params }),
}

