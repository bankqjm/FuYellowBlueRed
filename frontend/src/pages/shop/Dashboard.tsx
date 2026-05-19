import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Spin, Typography, Select } from 'antd'
import { ShoppingCartOutlined, DollarOutlined, ClockCircleOutlined, StarOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { shopApi, ShopStats, ShopTrendItem } from '../../services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

export default function Dashboard() {
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<ShopStats | null>(null)
  const [trendData, setTrendData] = useState<ShopTrendItem[]>([])
  const [trendDays, setTrendDays] = useState(7)
  const isMobile = useIsMobile()

  const fetchStats = async () => {
    try {
      setLoading(true)
      const res = await shopApi.getMyStats()
      setStats(res.data)
    } catch (error) {
      console.error('获取统计数据失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTrend = async () => {
    try {
      const res = await shopApi.getMyStatsTrend(trendDays)
      setTrendData(res.data)
    } catch (error) {
      console.error('获取趋势数据失败', error)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    fetchTrend()
  }, [trendDays])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  const statCards = [
    { title: '总订单', value: stats?.total_orders ?? 0, icon: <ShoppingCartOutlined />, color: '#1890ff' },
    { title: '总收入', value: stats?.total_revenue ?? 0, icon: <DollarOutlined />, color: '#52c41a', prefix: '¥' },
    { title: '待处理', value: stats?.pending_orders ?? 0, icon: <ClockCircleOutlined />, color: '#faad14' },
    { title: '评分', value: stats?.rating ?? 0, icon: <StarOutlined />, color: '#ff4d4f', suffix: '分' },
  ]

  const renderTrendChart = () => (
    <Card style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>趋势分析</Title>
        <Select
          value={trendDays}
          onChange={setTrendDays}
          size="small"
          style={{ width: 100 }}
          options={[
            { label: '近7天', value: 7 },
            { label: '近14天', value: 14 },
            { label: '近30天', value: 30 },
          ]}
        />
      </div>
      <ResponsiveContainer width="100%" height={isMobile ? 220 : 300}>
        <LineChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="orders" name="订单数" stroke="#1890ff" strokeWidth={2} dot={{ r: 3 }} />
          <Line yAxisId="right" type="monotone" dataKey="revenue" name="收入(元)" stroke="#52c41a" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )

  if (isMobile) {
    return (
      <div>
        <Card>
          <Title level={4}>数据看板</Title>
        </Card>
        <div className="mobile-stats-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
          {statCards.map((item) => (
            <Card key={item.title} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 28, color: item.color, marginBottom: 8 }}>{item.icon}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#333' }}>
                {item.prefix}{item.title === '总收入' ? (item.value as number).toFixed(2) : item.value}{item.suffix}
              </div>
              <div style={{ fontSize: 13, color: '#999', marginTop: 4 }}>{item.title}</div>
            </Card>
          ))}
        </div>
        {renderTrendChart()}
      </div>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4}>数据看板</Title>
      </Card>
      <Row gutter={16} style={{ marginTop: 16 }}>
        {statCards.map((item) => (
          <Col span={6} key={item.title}>
            <Card>
              <Statistic
                title={item.title}
                value={item.value}
                prefix={item.prefix === '¥' ? <><DollarOutlined /> ¥</> : item.icon}
                suffix={item.suffix}
                valueStyle={{ color: item.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>
      {renderTrendChart()}
    </div>
  )
}
