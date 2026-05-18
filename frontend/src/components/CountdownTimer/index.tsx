import { useState, useEffect, useCallback } from 'react'
import { Typography } from 'antd'

const { Text } = Typography

interface CountdownTimerProps {
  endTime: Date
  onExpire?: () => void
  warningThreshold?: number
  expiredText?: string
}

export function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export default function CountdownTimer({
  endTime,
  onExpire,
  warningThreshold = 300,
  expiredText = '已过期',
}: CountdownTimerProps) {
  const [remainingSeconds, setRemainingSeconds] = useState(() => {
    return Math.max(0, Math.floor((endTime.getTime() - Date.now()) / 1000))
  })

  const isWarning = remainingSeconds > 0 && remainingSeconds <= warningThreshold
  const isExpired = remainingSeconds <= 0

  const handleExpire = useCallback(() => {
    if (onExpire) {
      onExpire()
    }
  }, [onExpire])

  useEffect(() => {
    if (remainingSeconds <= 0) {
      handleExpire()
      return
    }

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        const next = prev - 1
        if (next <= 0) {
          clearInterval(timer)
          handleExpire()
          return 0
        }
        return next
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [remainingSeconds, handleExpire])

  if (isExpired) {
    return <Text type="secondary">{expiredText}</Text>
  }

  return (
    <Text
      style={{
        fontSize: 18,
        fontWeight: 600,
        color: isWarning ? '#ff4d4f' : '#333',
        fontFamily: 'monospace',
      }}
    >
      {formatTime(remainingSeconds)}
    </Text>
  )
}
