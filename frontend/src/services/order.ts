import api from './api'
import { OrderInfo, PageResponse } from './shop'

export interface CartItemInfo {
  id: number
  user_id: number
  shop_id: number
  product_id: number
  quantity: number
  created_at?: string
  product_name?: string
  product_image?: string
  product_price?: number
  shop_name?: string
}

export const cartApi = {
  getCart: () => api.get<CartItemInfo[]>('/orders/cart'),

  addToCart: (data: {
    shop_id: number
    product_id: number
    quantity: number
  }) => api.post<CartItemInfo>('/orders/cart', data),

  updateCartItem: (itemId: number, data: { quantity?: number }) =>
    api.put<CartItemInfo>(`/orders/cart/${itemId}`, data),

  deleteCartItem: (itemId: number) => api.delete(`/orders/cart/${itemId}`),

  clearShopCart: (shopId: number) => api.delete(`/orders/cart/shop/${shopId}`),
}

export const orderApi = {
  createOrder: (data: {
    address_id: number
    shop_id: number
    remark?: string
  }) => api.post<OrderInfo>('/orders/create', data),

  payOrder: (orderId: number) => api.post<OrderInfo>(`/orders/${orderId}/pay`),

  listOrders: (params?: {
    page?: number
    page_size?: number
    status?: string
  }) => api.get<PageResponse<OrderInfo>>('/orders', { params }),

  getOrderDetail: (orderId: number) => api.get<OrderInfo>(`/orders/${orderId}`),

  confirmReceipt: (orderId: number) => api.put<OrderInfo>(`/orders/${orderId}/confirm`),

  cancelOrder: (orderId: number) => api.put<OrderInfo>(`/orders/${orderId}/cancel`),
}
