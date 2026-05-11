import { Card, Typography, List, Empty, Button, Space } from 'antd'
import { EnvironmentOutlined, PlusOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function Addresses() {
  return (
    <Card
      title="收货地址"
      extra={<Button type="primary" icon={<PlusOutlined />}>新增地址</Button>}
    >
      <Empty
        description="暂无收货地址"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">* 地址管理功能将在 M3 阶段完善</Text>
      </div>
    </Card>
  )
}
