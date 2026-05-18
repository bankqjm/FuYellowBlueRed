const NOTIFICATION_PERMISSION_KEY = 'notification_permission_requested'

const STATUS_MESSAGES: Record<string, string> = {
  PENDING_ACCEPT: '商家正在确认您的订单',
  ACCEPTED: '商家已接单，正在准备中',
  READY: '订单已备好，等待骑手取餐',
  DELIVERING: '骑手正在配送中',
  COMPLETED: '订单已完成，祝您用餐愉快',
  CANCELLED: '订单已取消',
}

export function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    return Promise.resolve('denied' as NotificationPermission)
  }

  if (Notification.permission === 'granted') {
    return Promise.resolve('granted' as NotificationPermission)
  }

  if (Notification.permission === 'denied') {
    return Promise.resolve('denied' as NotificationPermission)
  }

  return Notification.requestPermission()
}

export function sendOrderNotification(orderNo: string, status: string, shopName?: string) {
  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return
  }

  const message = STATUS_MESSAGES[status]
  if (!message) return

  const title = shopName ? `${shopName} - 订单更新` : '订单状态更新'

  try {
    const notification = new Notification(title, {
      body: `订单 ${orderNo}: ${message}`,
      icon: '/favicon.ico',
      tag: `order-${orderNo}-${status}`,
    })

    notification.onclick = () => {
      window.focus()
      notification.close()
    }
  } catch {
    // Notification API may not be available in all contexts
  }
}

export function shouldRequestPermission(): boolean {
  if (!('Notification' in window)) return false
  if (Notification.permission !== 'default') return false
  return !sessionStorage.getItem(NOTIFICATION_PERMISSION_KEY)
}

export function markPermissionRequested() {
  sessionStorage.setItem(NOTIFICATION_PERMISSION_KEY, 'true')
}
