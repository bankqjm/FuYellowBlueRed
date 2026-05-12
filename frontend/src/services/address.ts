
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
  getAddresses: () =&gt; api.get&lt;AddressInfo[]&gt;('/users/addresses'),

  createAddress: (data: {
    contact_name: string
    contact_phone: string
    address: string
    latitude?: number
    longitude?: number
    is_default?: number
  }) =&gt; api.post&lt;AddressInfo&gt;('/users/addresses', data),

  updateAddress: (addressId: number, data: {
    contact_name?: string
    contact_phone?: string
    address?: string
    latitude?: number
    longitude?: number
    is_default?: number
  }) =&gt; api.put&lt;AddressInfo&gt;(`/users/addresses/${addressId}`, data),

  deleteAddress: (addressId: number) =&gt; api.delete(`/users/addresses/${addressId}`),
}

