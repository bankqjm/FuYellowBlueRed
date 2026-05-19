import { describe, it, expect, vi, beforeEach } from 'vitest'
import { orderApi, cartApi } from '@/services/order'
import axios from 'axios'

const mockedAxios = axios as jest.Mocked<typeof axios>

describe('Order API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('cartApi', () => {
    it('should call getCart API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: 'success',
          data: [
            {
              id: 1,
              user_id: 1,
              shop_id: 1,
              product_id: 1,
              quantity: 2,
              product_name: '测试商品',
              product_price: 25.0
            }
          ]
        }
      }
      mockedAxios.get = vi.fn().mockResolvedValue(mockResponse)

      const result = await cartApi.getCart()

      expect(mockedAxios.get).toHaveBeenCalledWith('/orders/cart')
      expect(result.data.data).toHaveLength(1)
      expect(result.data.data[0].product_name).toBe('测试商品')
    })

    it('should call addToCart API with correct params', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '添加成功',
          data: {
            id: 1,
            shop_id: 1,
            product_id: 1,
            quantity: 2,
            product_name: '测试商品'
          }
        }
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      const result = await cartApi.addToCart({
        shop_id: 1,
        product_id: 1,
        quantity: 2
      })

      expect(mockedAxios.post).toHaveBeenCalledWith('/orders/cart', {
        shop_id: 1,
        product_id: 1,
        quantity: 2
      })
      expect(result.data.data.quantity).toBe(2)
    })

    it('should call updateCartItem API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '更新成功',
          data: {
            id: 1,
            quantity: 5
          }
        }
      }
      mockedAxios.put = vi.fn().mockResolvedValue(mockResponse)

      const result = await cartApi.updateCartItem(1, { quantity: 5 })

      expect(mockedAxios.put).toHaveBeenCalledWith('/orders/cart/1', { quantity: 5 })
      expect(result.data.data.quantity).toBe(5)
    })

    it('should call deleteCartItem API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '删除成功'
        }
      }
      mockedAxios.delete = vi.fn().mockResolvedValue(mockResponse)

      await cartApi.deleteCartItem(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/orders/cart/1')
    })

    it('should call clearShopCart API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '清空成功'
        }
      }
      mockedAxios.delete = vi.fn().mockResolvedValue(mockResponse)

      await cartApi.clearShopCart(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/orders/cart/shop/1')
    })
  })

  describe('orderApi', () => {
    it('should call createOrder API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '创建订单成功',
          data: {
            id: 1,
            order_no: 'TEST123',
            total_amount: 55.0,
            status: 'PENDING_PAYMENT'
          }
        }
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.createOrder({
        address_id: 1,
        shop_id: 1,
        remark: '测试备注'
      })

      expect(mockedAxios.post).toHaveBeenCalledWith('/orders/create', {
        address_id: 1,
        shop_id: 1,
        remark: '测试备注'
      })
      expect(result.data.data.status).toBe('PENDING_PAYMENT')
    })

    it('should call payOrder API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '支付成功',
          data: {
            id: 1,
            status: 'PENDING_ACCEPT'
          }
        }
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.payOrder(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/orders/1/pay')
      expect(result.data.data.status).toBe('PENDING_ACCEPT')
    })

    it('should call listOrders API with filters', async () => {
      const mockResponse = {
        data: {
          code: 0,
          data: {
            items: [],
            total: 0,
            page: 1,
            page_size: 20
          }
        }
      }
      mockedAxios.get = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.listOrders({ page: 1, status: 'PENDING_PAYMENT' })

      expect(mockedAxios.get).toHaveBeenCalledWith('/orders', {
        params: { page: 1, status: 'PENDING_PAYMENT' }
      })
    })

    it('should call getOrderDetail API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          data: {
            id: 1,
            order_no: 'TEST123',
            items: []
          }
        }
      }
      mockedAxios.get = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.getOrderDetail(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/orders/1')
      expect(result.data.data.id).toBe(1)
    })

    it('should call confirmReceipt API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '确认收货成功',
          data: {
            id: 1,
            status: 'COMPLETED'
          }
        }
      }
      mockedAxios.put = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.confirmReceipt(1)

      expect(mockedAxios.put).toHaveBeenCalledWith('/orders/1/confirm')
      expect(result.data.data.status).toBe('COMPLETED')
    })

    it('should call cancelOrder API', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '取消订单成功',
          data: {
            id: 1,
            status: 'CANCELLED'
          }
        }
      }
      mockedAxios.put = vi.fn().mockResolvedValue(mockResponse)

      const result = await orderApi.cancelOrder(1)

      expect(mockedAxios.put).toHaveBeenCalledWith('/orders/1/cancel')
      expect(result.data.data.status).toBe('CANCELLED')
    })
  })
})
