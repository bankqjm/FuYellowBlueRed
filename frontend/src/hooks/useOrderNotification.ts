import { useEffect, useRef, useCallback } from 'react'
import { orderApi } from '../services/order'
import {
  requestNotificationPermission,
  sendOrderNotification,
  shouldRequestPermission,
  markPermissionRequested,
} from '../utils/notification'

const NOTIFIABLE_STATUSES = new Set([
  'PENDING_ACCEPT',
  'ACCEPTED',
  'READY',
  'DELIVERING',
  'COMPLETED',
  'CANCELLED',
])

const POLL_INTERVAL = 15000

export function useOrderNotification(isAuthenticated: boolean) {
  const prevOrdersRef = useRef<Map<number, string>>(new Map())
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const checkOrderUpdates = useCallback(async () => {
    if (!isAuthenticated) {return}

    try {
      const res = await orderApi.listOrders({ page: 1, page_size: 20 })
      const currentOrders = res.data.items
      const prevMap = prevOrdersRef.current
      const newMap = new Map<number, string>()

      for (const order of currentOrders) {
        newMap.set(order.id, order.status)

        const prevStatus = prevMap.get(order.id)
        if (prevStatus && prevStatus !== order.status && NOTIFIABLE_STATUSES.has(order.status)) {
          sendOrderNotification(order.order_no, order.status, order.shop_name)
        }
      }

      prevOrdersRef.current = newMap
    } catch {
      // Silently fail - notification is non-critical
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (!isAuthenticated) {
      prevOrdersRef.current.clear()
      return
    }

    if (shouldRequestPermission()) {
      requestNotificationPermission().then(() => {
        markPermissionRequested()
      })
    }

    checkOrderUpdates()

    timerRef.current = setInterval(checkOrderUpdates, POLL_INTERVAL)

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [isAuthenticated, checkOrderUpdates])
}
