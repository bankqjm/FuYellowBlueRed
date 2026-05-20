
import api from './api'
import { PageResponse } from './shop'

export interface WalletInfo {
  id: number
  balance: number
  frozen_balance: number
  total_income?: number
  total_expense?: number
}

export interface TransactionInfo {
  id: number
  type: string
  flow_type?: string
  business_type?: string
  amount: number
  balance_before: number
  balance_after: number
  description?: string
  created_at: string
}

export const walletApi = {
  getWallet: () => api.get<WalletInfo>('/wallet'),

  getTransactions: (params?: { page?: number; page_size?: number; business_type?: string; flow_type?: string }) =>
    api.get<PageResponse<TransactionInfo>>('/wallet/transactions', { params }),

  recharge: (amount: number) => api.post<any>('/wallet/recharge', { amount }),

  withdraw: (amount: number, method: string = 'ALIPAY', account: string = '') =>
    api.post<any>('/wallet/withdraw', { amount, method, account }),
}
