
import api from './api'
import { PageResponse } from './shop'

export interface WalletInfo {
  id: number
  balance: number
  frozen_balance: number
}

export interface TransactionInfo {
  id: number
  type: string
  amount: number
  balance_before: number
  balance_after: number
  description?: string
  created_at: string
}

export const walletApi = {
  getWallet: () => api.get<WalletInfo>('/wallet'),

  getTransactions: (params?: { page?: number; page_size?: number }) =>
    api.get<PageResponse<TransactionInfo>>('/wallet/transactions', { params }),
}
