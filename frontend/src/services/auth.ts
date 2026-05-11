import api from './api'

export interface LoginParams {
  phone: string
  password: string
}

export interface RegisterParams {
  phone: string
  password: string
  nickname?: string
  role?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: number
  role: string
  nickname?: string
  avatar?: string
}

export const authApi = {
  login: (data: LoginParams) => api.post<{ data: AuthResponse }>('/auth/login', data),
  register: (data: RegisterParams) => api.post('/auth/register', data),
}

export const userApi = {
  getMe: () => api.get('/users/me'),
  updateMe: (data: any) => api.put('/users/me', data),
}
