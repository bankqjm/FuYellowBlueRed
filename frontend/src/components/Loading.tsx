import { Spin, SpinProps, Typography } from 'antd'

const { Text } = Typography

interface LoadingProps extends SpinProps {
  tip?: string
  fullScreen?: boolean
}

const Loading: React.FC<LoadingProps> = ({
  tip = '加载中...',
  fullScreen = false,
  ...spinProps
}) => {
  if (fullScreen) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        flexDirection: 'column',
      }}>
        <Spin size="large" {...spinProps} />
        {tip && (
          <Text type="secondary" style={{ marginTop: 16 }}>
            {tip}
          </Text>
        )}
      </div>
    )
  }

  return <Spin tip={tip} {...spinProps} />
}

export default Loading
