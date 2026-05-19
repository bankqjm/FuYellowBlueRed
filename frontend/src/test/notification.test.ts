import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  requestNotificationPermission,
  sendOrderNotification,
  shouldRequestPermission,
  markPermissionRequested,
} from '@/utils/notification'

describe('Notification Utils', () => {
  let originalNotification: any

  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    originalNotification = window.Notification
  })

  afterEach(() => {
    window.Notification = originalNotification
  })

  describe('shouldRequestPermission', () => {
    it('should return false when Notification API is not available', () => {
      delete (window as any).Notification
      expect(shouldRequestPermission()).toBe(false)
    })

    it('should return false when permission is already granted', () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'granted' },
        writable: true,
        configurable: true,
      })

      expect(shouldRequestPermission()).toBe(false)
    })

    it('should return false when permission is already denied', () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'denied' },
        writable: true,
        configurable: true,
      })

      expect(shouldRequestPermission()).toBe(false)
    })

    it('should return false when already requested in session', () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'default' },
        writable: true,
        configurable: true,
      })
      sessionStorage.setItem('notification_permission_requested', 'true')

      expect(shouldRequestPermission()).toBe(false)
    })

    it('should return true when permission is default and not yet requested', () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'default' },
        writable: true,
        configurable: true,
      })

      expect(shouldRequestPermission()).toBe(true)
    })
  })

  describe('markPermissionRequested', () => {
    it('should set flag in sessionStorage', () => {
      markPermissionRequested()
      expect(sessionStorage.getItem('notification_permission_requested')).toBe('true')
    })
  })

  describe('sendOrderNotification', () => {
    it('should not throw when Notification API is not available', () => {
      delete (window as any).Notification
      expect(() => sendOrderNotification('ORD001', 'ACCEPTED')).not.toThrow()
    })

    it('should not create notification when permission is not granted', () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'denied' },
        writable: true,
        configurable: true,
      })

      expect(() => sendOrderNotification('ORD001', 'ACCEPTED')).not.toThrow()
    })
  })

  describe('requestNotificationPermission', () => {
    it('should return denied when Notification API is not available', async () => {
      delete (window as any).Notification
      const result = await requestNotificationPermission()
      expect(result).toBe('denied')
    })

    it('should return granted when permission already granted', async () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'granted' },
        writable: true,
        configurable: true,
      })

      const result = await requestNotificationPermission()
      expect(result).toBe('granted')
    })

    it('should return denied when permission already denied', async () => {
      Object.defineProperty(window, 'Notification', {
        value: { permission: 'denied' },
        writable: true,
        configurable: true,
      })

      const result = await requestNotificationPermission()
      expect(result).toBe('denied')
    })
  })
})
