import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import CountdownTimer, { formatTime } from '@/components/CountdownTimer'

describe('CountdownTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  describe('formatTime', () => {
    it('should format seconds correctly', () => {
      expect(formatTime(0)).toBe('00:00')
      expect(formatTime(59)).toBe('00:59')
      expect(formatTime(60)).toBe('01:00')
      expect(formatTime(65)).toBe('01:05')
      expect(formatTime(125)).toBe('02:05')
      expect(formatTime(3600)).toBe('60:00')
      expect(formatTime(3661)).toBe('61:01')
    })

    it('should pad single digits with zero', () => {
      expect(formatTime(5)).toBe('00:05')
      expect(formatTime(65)).toBe('01:05')
      expect(formatTime(601)).toBe('10:01')
    })
  })

  describe('CountdownTimer component', () => {
    it('should render with initial time', () => {
      const futureTime = new Date(Date.now() + 5 * 60 * 1000)
      render(<CountdownTimer endTime={futureTime} />)
      expect(screen.getByText('05:00')).toBeInTheDocument()
    })

    it('should show expired text when time is up', () => {
      const pastTime = new Date(Date.now() - 1000)
      render(<CountdownTimer endTime={pastTime} expiredText="已过期" />)
      expect(screen.getByText('已过期')).toBeInTheDocument()
    })

    it('should call onExpire callback when time expires', () => {
      vi.useFakeTimers()
      const onExpire = vi.fn()
      const futureTime = new Date(Date.now() + 100)
      render(<CountdownTimer endTime={futureTime} onExpire={onExpire} />)

      act(() => {
        vi.advanceTimersByTime(200)
      })
      expect(onExpire).toHaveBeenCalled()
    })

    it('should update countdown every second', () => {
      vi.useFakeTimers()
      const futureTime = new Date(Date.now() + 3 * 1000)
      render(<CountdownTimer endTime={futureTime} />)

      act(() => {
        vi.advanceTimersByTime(1000)
      })
      const timeElement = screen.getByText(/00:0[23]/)
      expect(timeElement).toBeInTheDocument()
    })
  })
})
