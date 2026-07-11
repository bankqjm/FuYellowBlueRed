import { useState, useEffect, useRef } from 'react'
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
  const initialSeconds = Math.max(0, Math.floor((endTime.getTime() - Date.now()) / 1000))

  const remainingRef = useRef(initialSeconds)
  const [displaySeconds, setDisplaySeconds] = useState(initialSeconds)
  const expiredRef = useRef(false)

  const isWarning = displaySeconds > 0 && displaySeconds <= warningThreshold
  const isExpired = displaySeconds <= 0

  useEffect(() => {
    if (initialSeconds <= 0) {
      if (!expiredRef.current) {
        expiredRef.current = true
        onExpire?.()
      }
      return
    }

    const interval = setInterval(() => {
      remainingRef.current -= 1
      if (remainingRef.current <= 0) {
        remainingRef.current = 0
        setDisplaySeconds(0)
        clearInterval(interval)
        if (!expiredRef.current) {
          expiredRef.current = true
          onExpire?.()
        }
      } else {
        setDisplaySeconds(remainingRef.current)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [initialSeconds, onExpire])

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
      {formatTime(displaySeconds)}
    </Text>
  )
}
