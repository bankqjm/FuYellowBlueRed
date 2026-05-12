import { useState, useCallback, useMemo, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { orderApi } from '../services/order'
import type { OrderInfo, PageResponse } from '../services/shop'

export const useOrders = (initialStatus?: string) => {
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<string | undefined>(initialStatus)

  const fetchOrders = useCallback(async (currentPage: number = 1, pageSize: number = 20) => {
    try {
      setLoading(true)
      const res = await orderApi.getOrders({
        status,
        page: currentPage,
        pageSize,
      })
      setOrders(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取订单失败', error)
    } finally {
      setLoading(false)
    }
  }, [status])

  useEffect(() => {
    fetchOrders()
  }, [fetchOrders])

  return {
    orders,
    total,
    loading,
    status,
    setStatus,
    refetch: fetchOrders,
  }
}
