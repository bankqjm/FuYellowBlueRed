import { describe, it, expect, vi, beforeEach, Mocked } from 'vitest'
import api from '@/services/api'
import { favoritesApi } from '@/services/favorites'

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedApi = api as Mocked<typeof api>

describe('Favorites API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('addFavorite', () => {
    it('should call add favorite API', async () => {
      mockedApi.post = vi.fn().mockResolvedValue({
        code: 0,
        message: '收藏成功',
        data: null,
      })

      await favoritesApi.addFavorite(1)
      expect(mockedApi.post).toHaveBeenCalledWith('/favorites/1')
    })
  })

  describe('removeFavorite', () => {
    it('should call remove favorite API', async () => {
      mockedApi.delete = vi.fn().mockResolvedValue({
        code: 0,
        message: '取消收藏成功',
        data: null,
      })

      await favoritesApi.removeFavorite(1)
      expect(mockedApi.delete).toHaveBeenCalledWith('/favorites/1')
    })
  })

  describe('checkFavorite', () => {
    it('should call check favorite API', async () => {
      mockedApi.get = vi.fn().mockResolvedValue({
        code: 0,
        data: { is_favorited: true },
      })

      const result = await favoritesApi.checkFavorite(1)
      expect(mockedApi.get).toHaveBeenCalledWith('/favorites/check/1')
      expect(result.data.is_favorited).toBe(true)
    })
  })

  describe('listFavorites', () => {
    it('should call list favorites API with pagination', async () => {
      mockedApi.get = vi.fn().mockResolvedValue({
        code: 0,
        data: { items: [], total: 0, page: 1, page_size: 20 },
      })

      await favoritesApi.listFavorites({ page: 1, page_size: 20 })
      expect(mockedApi.get).toHaveBeenCalledWith('/favorites', { params: { page: 1, page_size: 20 } })
    })
  })
})
