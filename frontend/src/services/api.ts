import axios from 'axios'
import { message } from 'antd'
import { useAuthStore } from '@/stores/authStore'

/** Read csrf_token from cookie (set by backend on login, non-HttpOnly) */
function getCsrfTokenFromCookie(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

api.interceptors.request.use(
  (config) => {
    // SEC-REFORM-05: Add CSRF token header for mutating requests
    const method = (config.method || 'get').toUpperCase()
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      const csrfToken = getCsrfTokenFromCookie()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 0) {
      message.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return response.data
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      const { logout } = useAuthStore.getState()
      logout()
      window.location.href = '/login'
      message.error('登录已过期，请重新登录')
    } else if (status === 403) {
      const errCode = error.response?.data?.error_code
      if (errCode === 'CSRF_FAILED') {
        message.error('安全验证失败，请刷新页面重试')
      } else {
        message.error('权限不足，无法访问该资源')
      }
    } else {
      message.error(error.response?.data?.message || error.message || '网络错误')
    }
    return Promise.reject(error)
  },
)

export default api
