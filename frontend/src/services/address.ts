
import api from './api'

export interface AddressInfo {
  id: number
  user_id: number
  contact_name: string
  contact_phone: string
  address: string
  latitude?: number
  longitude?: number
  is_default: number
  created_at?: string
}

export const addressApi = {
  getAddresses: () => api.get<AddressInfo[]>('/users/addresses'),

  createAddress: (data: {
    contact_name: string
    contact_phone: string
    address: string
    latitude?: number
    longitude?: number
    is_default?: number
  }) => api.post<AddressInfo>('/users/addresses', data),

  updateAddress: (addressId: number, data: {
    contact_name?: string
    contact_phone?: string
    address?: string
    latitude?: number
    longitude?: number
    is_default?: number
  }) => api.put<AddressInfo>(`/users/addresses/${addressId}`, data),

  deleteAddress: (addressId: number) => api.delete(`/users/addresses/${addressId}`),
}
