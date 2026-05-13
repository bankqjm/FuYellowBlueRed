
import { useState, useEffect } from 'react'
import { Card, Typography, Row, Col, Statistic, Spin } from 'antd'
import { ShoppingCartOutlined, UserOutlined, ShopOutlined, DollarOutlined } from '@ant-design/icons'
import api from '../../services/api'
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
  const isMobile = useIsMobile()

  useEffect(() => {
    fetchStats()
  }, [])

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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

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
    </div>
  )
}
