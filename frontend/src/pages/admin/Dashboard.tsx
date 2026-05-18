import { useState, useEffect } from 'react'
import { Card, Typography, Row, Col, Statistic, Spin, Select } from 'antd'
import { ShoppingCartOutlined, UserOutlined, ShopOutlined, DollarOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import { adminApi, AdminTrendItem } from '../../services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

interface Stats {
  user_count: number
  shop_count: number
  approved_shop_count: number
  order_count: number
  pending_order_count: number
}

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats | null>(null)
  const [trendData, setTrendData] = useState<AdminTrendItem[]>([])
  const [trendDays, setTrendDays] = useState(7)
  const isMobile = useIsMobile()

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    fetchTrend()
  }, [trendDays])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const res = await api.get<Stats>('/admin/stats')
      setStats(res.data)
    } catch (error) {
      console.error('获取统计数据失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTrend = async () => {
    try {
      const res = await adminApi.getStatsTrend(trendDays)
      setTrendData(res.data)
    } catch (error) {
      console.error('获取趋势数据失败', error)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

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
          <Line yAxisId="left" type="monotone" dataKey="new_users" name="新增用户" stroke="#722ed1" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )

  if (isMobile) {
    return (
      <div>
        <Title level={5}>平台概览</Title>
        <div className="mobile-stats-grid">
          <div className="stat-card">
            <div className="stat-value"><UserOutlined /> {stats?.user_count || 0}</div>
            <div className="stat-label">用户总数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value"><ShopOutlined /> {stats?.shop_count || 0}</div>
            <div className="stat-label">商家总数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#3f8600' }}><ShopOutlined /> {stats?.approved_shop_count || 0}</div>
            <div className="stat-label">已审核商家</div>
          </div>
          <div className="stat-card">
            <div className="stat-value"><ShoppingCartOutlined /> {stats?.order_count || 0}</div>
            <div className="stat-label">订单总数</div>
          </div>
        </div>
        <div className="mobile-card" style={{ textAlign: 'center' }}>
          <div className="stat-value" style={{ color: '#cf1322' }}><DollarOutlined /> {stats?.pending_order_count || 0}</div>
          <div className="stat-label">进行中订单</div>
        </div>
        {renderTrendChart()}
      </div>
    )
  }

  return (
    <div>
      <Title level={4}>平台概览</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="用户总数"
              value={stats?.user_count || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="商家总数"
              value={stats?.shop_count || 0}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已审核商家"
              value={stats?.approved_shop_count || 0}
              prefix={<ShopOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="订单总数"
              value={stats?.order_count || 0}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="进行中订单"
              value={stats?.pending_order_count || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>
      {renderTrendChart()}
    </div>
  )
}
