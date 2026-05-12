
import api from './api'

export interface ShopInfo {
  id: number
  user_id: number
  name: string
  logo?: string
  address: string
  latitude?: number
  longitude?: number
  business_hours?: string
  notice?: string
  rating: number
  status: number
  created_at: string
  updated_at: string
}

export interface CategoryInfo {
  id: number
  shop_id: number
  name: string
  sort_order: number
  created_at: string
  products?: ProductInfo[]
}

export interface ProductInfo {
  id: number
  shop_id: number
  category_id?: number
  name: string
  image?: string
  price: number
  original_price?: number
  description?: string
  stock: number
  sales: number
  status: number
  created_at: string
  updated_at: string
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface OrderItemInfo {
  id: number
  order_id: number
  product_id: number
  product_name: string
  product_image?: string
  price: number
  quantity: number
}

export interface AddressInfo {
  contact_name: string
  contact_phone: string
  address: string
}

export interface OrderInfo {
  id: number
  order_no: string
  user_id: number
  shop_id: number
  rider_id?: number
  address: string
  latitude?: number
  longitude?: number
  phone: string
  remark?: string
  total_amount: number
  delivery_fee: number
  status: string
  created_at?: string
  updated_at?: string
  shop_name?: string
  shop_image?: string
  items?: OrderItemInfo[]
  address_info?: AddressInfo
}

export interface ShopDetail extends ShopInfo {
  categories?: CategoryInfo[]
}

export const shopApi = {
  apply: (data: {
    name: string
    logo?: string
    address: string
    latitude?: number
    longitude?: number
    business_hours?: string
    notice?: string
  }) => api.post&lt;ShopInfo&gt;('/shop/apply', data),

  getMyShop: () => api.get&lt;ShopInfo&gt;('/shop/my'),

  updateMyShop: (data: {
    name?: string
    logo?: string
    address?: string
    latitude?: number
    longitude?: number
    business_hours?: string
    notice?: string
  }) => api.put&lt;ShopInfo&gt;('/shop/my', data),

  listShops: (params?: {
    page?: number
    page_size?: number
    keyword?: string
    status?: number
  }) => api.get&lt;PageResponse&lt;ShopInfo&gt;&gt;('/shop/list', { params }),

  getShopDetail: (shopId: number) => api.get&lt;ShopDetail&gt;(`/shop/${shopId}`),

  createCategory: (data: { shop_id: number; name: string; sort_order?: number }) =>
    api.post&lt;CategoryInfo&gt;('/shop/category', data),

  listCategories: (shopId: number) => api.get&lt;CategoryInfo[]&gt;(`/shop/category/${shopId}`),

  updateCategory: (categoryId: number, data: { name?: string; sort_order?: number }) =>
    api.put&lt;CategoryInfo&gt;(`/shop/category/${categoryId}`, data),

  deleteCategory: (categoryId: number) => api.delete(`/shop/category/${categoryId}`),

  createProduct: (data: {
    shop_id: number
    category_id?: number
    name: string
    image?: string
    price: number
    original_price?: number
    description?: string
    stock: number
  }) => api.post&lt;ProductInfo&gt;('/shop/product', data),

  listProducts: (shopId: number, params?: {
    page?: number
    page_size?: number
    keyword?: string
    category_id?: number
    status?: number
  }) => api.get&lt;PageResponse&lt;ProductInfo&gt;&gt;(`/shop/product/${shopId}`, { params }),

  getProductDetail: (productId: number) => api.get&lt;ProductInfo&gt;(`/shop/product/detail/${productId}`),

  updateProduct: (productId: number, data: {
    category_id?: number
    name?: string
    image?: string
    price?: number
    original_price?: number
    description?: string
    stock?: number
    status?: number
  }) => api.put&lt;ProductInfo&gt;(`/shop/product/${productId}`, data),

  deleteProduct: (productId: number) => api.delete(`/shop/product/${productId}`),

  getShopOrders: (params?: {
    page?: number
    page_size?: number
    status?: string
  }) => api.get&lt;PageResponse&lt;OrderInfo&gt;&gt;('/shop/my/orders', { params }),

  getShopOrderDetail: (orderId: number) => api.get&lt;OrderInfo&gt;(`/shop/my/orders/${orderId}`),

  acceptOrder: (orderId: number) => api.put&lt;OrderInfo&gt;(`/shop/my/orders/${orderId}/accept`),

  rejectOrder: (orderId: number) => api.put&lt;OrderInfo&gt;(`/shop/my/orders/${orderId}/reject`),

  orderReady: (orderId: number) => api.put&lt;OrderInfo&gt;(`/shop/my/orders/${orderId}/ready`),
}

export const adminApi = {
  approveShop: (shopId: number) => api.put&lt;ShopInfo&gt;(`/admin/shop/${shopId}/approve`),
  rejectShop: (shopId: number) => api.put&lt;ShopInfo&gt;(`/admin/shop/${shopId}/reject`),
  listPendingShops: (params?: { page?: number; page_size?: number; keyword?: string }) =>
    api.get&lt;PageResponse&lt;ShopInfo&gt;&gt;('/admin/shop/pending', { params }),
}

