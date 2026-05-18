
import api from './api'
import { PageResponse } from './shop'

export interface FavoriteShop {
  id: number
  shop_id: number
  created_at: string
  shop_name: string
  shop_image?: string
  shop_rating?: number
  monthly_sales?: number
  delivery_time?: number
  min_order_amount?: number
}

export const favoritesApi = {
  listFavorites: (params?: { page?: number; page_size?: number }) =>
    api.get<PageResponse<FavoriteShop>>('/favorites', { params }),

  addFavorite: (shopId: number) => api.post(`/favorites/${shopId}`),

  removeFavorite: (shopId: number) => api.delete(`/favorites/${shopId}`),

  checkFavorite: (shopId: number) => api.get<{ is_favorited: boolean }>(`/favorites/check/${shopId}`),
}
