import { describe, it, expect, vi, beforeEach, Mocked } from 'vitest'
import { authApi } from '@/services/auth'
import axios from 'axios'

const mockedAxios = axios as Mocked<typeof axios>

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should call login API with correct params', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '登录成功',
          data: {
            access_token: 'test-token',
            token_type: 'Bearer',
            user_id: 1,
            role: 'USER',
            nickname: '测试用户',
          },
        },
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      const result = await authApi.login({
        phone: '13800138000',
        password: 'Test123456',
      })

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/login', {
        phone: '13800138000',
        password: 'Test123456',
      })
      expect((result as any).data.data.access_token).toBe('test-token')
    })

    it('should handle login errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            code: 400,
            message: '用户名或密码错误',
          },
        },
      }
      mockedAxios.post = vi.fn().mockRejectedValue(mockError)

      await expect(
        authApi.login({
          phone: '13800138000',
          password: 'wrong-password',
        }),
      ).rejects.toEqual(mockError)
    })
  })

  describe('register', () => {
    it('should call register API with correct params', async () => {
      const mockResponse = {
        data: {
          code: 0,
          message: '注册成功',
          data: {
            id: 1,
            phone: '13800138001',
          },
        },
      }
      mockedAxios.post = vi.fn().mockResolvedValue(mockResponse)

      const result = await authApi.register({
        phone: '13800138001',
        password: 'Test123456',
        confirm_password: 'Test123456',
        role: 'USER',
      } as any)

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/register', {
        phone: '13800138001',
        password: 'Test123456',
        confirm_password: 'Test123456',
        role: 'USER',
      })
      expect((result as any).data.data.id).toBe(1)
    })

    it('should handle register validation errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            code: 400,
            message: '手机号已注册',
          },
        },
      }
      mockedAxios.post = vi.fn().mockRejectedValue(mockError)

      await expect(
        authApi.register({
          phone: '13800138000',
          password: 'Test123456',
          confirm_password: 'Test123456',
        } as any),
      ).rejects.toEqual(mockError)
    })
  })
})
