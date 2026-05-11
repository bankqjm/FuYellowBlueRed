
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

export const shopApi = {
  apply: (data: {
    name: string
    logo?: string
    address: string
    latitude?: number
    longitude?: number
    business_hours?: string
    notice?: string
  }) =&gt; api.post&lt;ShopInfo&gt;('/shop/apply', data),

  getMyShop: () =&gt; api.get&lt;ShopInfo&gt;('/shop/my'),

  updateMyShop: (data: {
    name?: string
    logo?: string
    address?: string
    latitude?: number
    longitude?: number
    business_hours?: string
    notice?: string
  }) =&gt; api.put&lt;ShopInfo&gt;('/shop/my', data),

  listShops: (params?: {
    page?: number
    page_size?: number
    keyword?: string
    status?: number
  }) =&gt; api.get&lt;PageResponse&lt;ShopInfo&gt;&gt;('/shop/list', { params }),

  getShopDetail: (shopId: number) =&gt; api.get&lt;ShopDetail&gt;(`/shop/${shopId}`),

  createCategory: (data: { shop_id: number; name: string; sort_order?: number }) =&gt;
    api.post&lt;CategoryInfo&gt;('/shop/category', data),

  listCategories: (shopId: number) =&gt; api.get&lt;CategoryInfo[]&gt;(`/shop/category/${shopId}`),

  updateCategory: (categoryId: number, data: { name?: string; sort_order?: number }) =&gt;
    api.put&lt;CategoryInfo&gt;(`/shop/category/${categoryId}`, data),

  deleteCategory: (categoryId: number) =&gt; api.delete(`/shop/category/${categoryId}`),

  createProduct: (data: {
    shop_id: number
    category_id?: number
    name: string
    image?: string
    price: number
    original_price?: number
    description?: string
    stock: number
  }) =&gt; api.post&lt;ProductInfo&gt;('/shop/product', data),

  listProducts: (shopId: number, params?: {
    page?: number
    page_size?: number
    keyword?: string
    category_id?: number
    status?: number
  }) =&gt; api.get&lt;PageResponse&lt;ProductInfo&gt;&gt;(`/shop/product/${shopId}`, { params }),

  getProductDetail: (productId: number) =&gt; api.get&lt;ProductInfo&gt;(`/shop/product/detail/${productId}`),

  updateProduct: (productId: number, data: {
    category_id?: number
    name?: string
    image?: string
    price?: number
    original_price?: number
    description?: string
    stock?: number
    status?: number
  }) =&gt; api.put&lt;ProductInfo&gt;(`/shop/product/${productId}`, data),

  deleteProduct: (productId: number) =&gt; api.delete(`/shop/product/${productId}`),
}

export interface ShopDetail extends ShopInfo {
  categories?: CategoryInfo[]
}

export const adminApi = {
  approveShop: (shopId: number) =&gt; api.put&lt;ShopInfo&gt;(`/admin/shop/${shopId}/approve`),
  rejectShop: (shopId: number) =&gt; api.put&lt;ShopInfo&gt;(`/admin/shop/${shopId}/reject`),
  listPendingShops: (params?: { page?: number; page_size?: number; keyword?: string }) =&gt;
    api.get&lt;PageResponse&lt;ShopInfo&gt;&gt;('/admin/shop/pending', { params }),
}

