
import { useState, useEffect } from 'react'
import { Card, Typography, Statistic, Row, Col, List, Empty, Spin } from 'antd'
import { WalletOutlined, AccountBookOutlined } from '@ant-design/icons'
import { riderApi, EarningsInfo, EarningsSummary } from '../../services/rider'

const { Title, Text } = Typography

export default function RiderEarnings() {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<EarningsSummary | null>(null)
  const [earnings, setEarnings] = useState<EarningsInfo[]>([])

  const fetchSummary = async () => {
    try {
      const res = await riderApi.getEarningsSummary()
      setSummary(res.data)
    } catch (error) {
      console.error('获取收入汇总失败', error)
    }
  }

  const fetchEarnings = async () => {
    try {
      setLoading(true)
      const res = await riderApi.getEarnings()
      setEarnings(res.data.items)
    } catch (error) {
      console.error('获取收入明细失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
    fetchEarnings()
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4}>我的收入</Title>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic
              title="累计收入"
              value={summary?.total_earnings || 0}
              prefix={<AccountBookOutlined />}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic
              title="可提现余额"
              value={summary?.balance || 0}
              prefix={<WalletOutlined />}
              precision={2}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 16 }}>
        <Title level={5}>收入明细</Title>
        {earnings.length === 0 ? (
          <Empty description="暂无收入记录" style={{ marginTop: 50 }} />
        ) : (
          <List
            dataSource={earnings}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={`订单 #${item.order_id}`}
                  description={item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                />
                <Text type="success" strong>+¥{item.amount.toFixed(2)}</Text>
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  )
}

