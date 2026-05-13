import { useState, useCallback, useEffect } from 'react'
import { addressApi } from '../services/address'

export const useAddresses = () => {
  const [addresses, setAddresses] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAddresses = useCallback(async () => {
    try {
      setLoading(true)
      const res = await addressApi.getAddresses()
      setAddresses(res.data)
    } catch (error) {
      console.error('获取地址失败', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const addAddress = useCallback(async (address: any) => {
    try {
      const res = await addressApi.createAddress(address)
      await fetchAddresses()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchAddresses])

  const updateAddress = useCallback(async (id: number, address: any) => {
    try {
      const res = await addressApi.updateAddress(id, address)
      await fetchAddresses()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchAddresses])

  const deleteAddress = useCallback(async (id: number) => {
    try {
      await addressApi.deleteAddress(id)
      await fetchAddresses()
    } catch (error) {
      throw error
    }
  }, [fetchAddresses])

  useEffect(() => {
    fetchAddresses()
  }, [fetchAddresses])

  return {
    addresses,
    loading,
    fetchAddresses,
    addAddress,
    updateAddress,
    deleteAddress,
  }
}
