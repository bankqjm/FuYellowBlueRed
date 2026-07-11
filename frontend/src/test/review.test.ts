import { describe, it, expect, vi, beforeEach, Mocked } from 'vitest'
import { reviewApi } from '@/services/review'
import axios from 'axios'

const mockedAxios = axios as Mocked<typeof axios>

describe('Review API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createReview', () => {
    it('should call create review API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          data: { id: 1, order_id: 1, shop_rating: 5, content: '好评' },
        },
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      await reviewApi.createReview({
        order_id: 1,
        shop_rating: 5,
        content: '好评',
      })

      expect(mockedAxios.post).toHaveBeenCalledWith('/reviews', {
        order_id: 1,
        shop_rating: 5,
        content: '好评',
      })
    })
  })

  describe('getShopReviews', () => {
    it('should call get shop reviews API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          data: { items: [{ id: 1, shop_rating: 5, content: '好吃' }], total: 1, page: 1, page_size: 10 },
        },
      }
      mockedAxios.get = vi.fn().mockResolvedValue(mockResponse)

      await reviewApi.getShopReviews(1, { page: 1, page_size: 10 })
      expect(mockedAxios.get).toHaveBeenCalledWith('/reviews/shop/1', { params: { page: 1, page_size: 10 } })
    })
  })

  describe('getOrderReview', () => {
    it('should call get order review API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          data: { id: 1, order_id: 1, shop_rating: 4, content: '不错' },
        },
      }
      mockedAxios.get = vi.fn().mockResolvedValue(mockResponse)

      await reviewApi.getOrderReview(1)
      expect(mockedAxios.get).toHaveBeenCalledWith('/reviews/order/1')
    })
  })
})
