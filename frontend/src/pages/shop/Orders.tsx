import { Card, Typography, Tabs, List, Empty, Button, Space, Tag } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const { TabPane } = Tabs

export default function ShopOrders() {
  return (
    <Card>
      <Title level={4}>订单管理</Title>
      <Tabs defaultActiveKey="pending">
        <TabPane tab="待接单" key="pending">
          <Empty description="暂无待接单订单" />
        </TabPane>
        <TabPane tab="备餐中" key="preparing">
          <Empty description="暂无备餐中订单" />
        </TabPane>
        <TabPane tab="已完成" key="completed">
          <Empty description="暂无已完成订单" />
        </TabPane>
      </Tabs>
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">* 商家订单管理将在 M2-M3 阶段完善</Text>
      </div>
    </Card>
  )
}
