import { describe, it, expect, vi, beforeEach, Mocked } from 'vitest'
import api from '@/services/api'
import { walletApi } from '@/services/wallet'

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockedApi = api as Mocked<typeof api>

describe('Wallet API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getWallet', () => {
    it('should call get wallet API', async () => {
      mockedApi.get = vi.fn().mockResolvedValue({
        code: 0,
        data: { balance: 100.50, total_income: 500, total_expense: 399.50 },
      })

      const result = await walletApi.getWallet()
      expect(mockedApi.get).toHaveBeenCalledWith('/wallet')
      expect(result.data.balance).toBe(100.50)
    })
  })

  describe('getTransactions', () => {
    it('should call get transactions API with params', async () => {
      mockedApi.get = vi.fn().mockResolvedValue({
        code: 0,
        data: { items: [], total: 0, page: 1, page_size: 20 },
      })

      await walletApi.getTransactions({ page: 1, page_size: 20 })
      expect(mockedApi.get).toHaveBeenCalledWith('/wallet/transactions', { params: { page: 1, page_size: 20 } })
    })
  })

  describe('withdraw', () => {
    it('should call withdraw API', async () => {
      mockedApi.post = vi.fn().mockResolvedValue({
        code: 0,
        message: '提现申请已提交',
      })

      await walletApi.withdraw(100)
      expect(mockedApi.post).toHaveBeenCalledWith('/wallet/withdraw', { amount: 100, method: 'ALIPAY', account: '' })
    })
  })
})
