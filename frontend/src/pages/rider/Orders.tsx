import { Card, Typography, Tabs, List, Empty, Button, Space, Tag } from 'antd'
import { InboxOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const { TabPane } = Tabs

export default function RiderOrders() {
  return (
    <Card>
      <Title level={4}>骑手接单</Title>
      <Tabs defaultActiveKey="pending">
        <TabPane tab="待接单" key="pending">
          <Empty description="暂无待接单订单" />
        </TabPane>
        <TabPane tab="进行中" key="active">
          <Empty description="暂无进行中订单" />
        </TabPane>
      </Tabs>
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">* 骑手接单功能将在 M4 阶段完善</Text>
      </div>
    </Card>
  )
}
