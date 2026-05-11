import { Card, Tabs, List, Empty, Typography } from 'antd'

const { Title, Text } = Typography

const { TabPane } = Tabs

export default function Orders() {
  return (
    <Card>
      <Title level={4}>我的订单</Title>
      <Tabs defaultActiveKey="all">
        <TabPane tab="全部" key="all">
          <Empty description="暂无订单" />
        </TabPane>
        <TabPane tab="待支付" key="pending">
          <Empty description="暂无待支付订单" />
        </TabPane>
        <TabPane tab="配送中" key="delivering">
          <Empty description="暂无配送中订单" />
        </TabPane>
        <TabPane tab="已完成" key="completed">
          <Empty description="暂无已完成订单" />
        </TabPane>
      </Tabs>
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">* 订单功能将在 M3 阶段完善</Text>
      </div>
    </Card>
  )
}
