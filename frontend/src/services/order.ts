
import api from './api'
import { OrderItemInfo, OrderInfo, PageResponse } from './shop'

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
  getCart: () =&gt; api.get&lt;CartItemInfo[]&gt;('/orders/cart'),

  addToCart: (data: {
    shop_id: number
    product_id: number
    quantity: number
  }) =&gt; api.post&lt;CartItemInfo&gt;('/orders/cart', data),

  updateCartItem: (itemId: number, data: { quantity?: number }) =&gt;
    api.put&lt;CartItemInfo&gt;(`/orders/cart/${itemId}`, data),

  deleteCartItem: (itemId: number) =&gt; api.delete(`/orders/cart/${itemId}`),

  clearShopCart: (shopId: number) =&gt; api.delete(`/orders/cart/shop/${shopId}`),
}

export const orderApi = {
  createOrder: (data: {
    address_id: number
    shop_id: number
    remark?: string
  }) =&gt; api.post&lt;OrderInfo&gt;('/orders/create', data),

  payOrder: (orderId: number) =&gt; api.post&lt;OrderInfo&gt;(`/orders/${orderId}/pay`),

  listOrders: (params?: {
    page?: number
    page_size?: number
    status?: string
  }) =&gt; api.get&lt;PageResponse&lt;OrderInfo&gt;&gt;('/orders', { params }),

  getOrderDetail: (orderId: number) =&gt; api.get&lt;OrderInfo&gt;(`/orders/${orderId}`),

  confirmReceipt: (orderId: number) =&gt; api.put&lt;OrderInfo&gt;(`/orders/${orderId}/confirm`),
}

