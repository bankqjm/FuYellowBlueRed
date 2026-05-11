import { Card, Typography, Row, Col, Statistic } from 'antd'
import { ShoppingCartOutlined, UserOutlined, ShopOutlined } from '@ant-design/icons'

const { Title } = Typography

export default function AdminDashboard() {
  return (
    <div>
      <Title level={4}>平台概览</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日订单"
              value={0}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="用户总数"
              value={0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="商家总数"
              value={0}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="骑手总数"
              value={0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>
      <div style={{ marginTop: 24 }}>
        <p style={{ color: '#999' }}>* 统计数据将在 M5 阶段完善</p>
      </div>
    </div>
  )
}
