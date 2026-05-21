import { useState, useEffect } from 'react'
import { Card, Typography, Row, Col, Statistic, Spin, Empty, Button } from 'antd'
import { ShoppingCartOutlined, DollarOutlined, ClockCircleOutlined, StarOutlined, ShopOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { shopApi } from '../../services/shop'
import { useNavigate } from 'react-router-dom'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

interface ShopStats {
  total_orders: number
  total_income: number
  pending_orders: number
  avg_rating: number
}

interface TrendItem {
  date: string
  orders: number
  income: number
}

export default function ShopDashboard() {
  const [loading, setLoading] = useState(true)
  const [hasShop, setHasShop] = useState<boolean | null>(null)
  const [stats, setStats] = useState<ShopStats | null>(null)
  const [trendData, setTrendData] = useState<TrendItem[]>([])
  const navigate = useNavigate()
  const isMobile = useIsMobile()

  useEffect(() => {
    checkShopAndFetchData()
  }, [])

  const checkShopAndFetchData = async () => {
    try {
      setLoading(true)
      const shopRes = await shopApi.getMyShop()
      if (!shopRes.data) {
        setHasShop(false)
        return
      }
      setHasShop(true)
      try {
        const statsRes = await shopApi.getMyStats()
        setStats(statsRes.data)
      } catch {
        // Stats may fail, show zeros
      }
      try {
        const trendRes = await shopApi.getMyStatsTrend(7)
        setTrendData(trendRes.data)
      } catch {
        // Trend may fail, show empty
      }
    } catch {
      setHasShop(false)
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

  if (!hasShop) {
    return (
      <div style={{ textAlign: 'center', padding: isMobile ? 40 : 80 }}>
        <Empty
          image={<ShopOutlined style={{ fontSize: 64, color: '#1890ff' }} />}
          description={
            <div>
              <Title level={4} style={{ marginBottom: 8 }}>欢迎入驻！</Title>
              <p style={{ color: '#8c8c8c', marginBottom: 24 }}>创建您的店铺，即可管理商品、接单和查看经营数据</p>
            </div>
          }
        >
          <Button type="primary" size="large" onClick={() => navigate('/shop/info')}>
            创建我的店铺
          </Button>
        </Empty>
      </div>
    )
  }

  const renderTrendChart = () => (
    <Card style={{ marginTop: 16 }}>
      <Title level={5} style={{ marginBottom: 16 }}>近7天趋势</Title>
      {trendData.length === 0 ? (
        <Empty description="暂无趋势数据" />
      ) : (
        <ResponsiveContainer width="100%" height={isMobile ? 220 : 300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="orders" name="订单数" stroke="#1890ff" strokeWidth={2} dot={{ r: 3 }} />
            <Line yAxisId="right" type="monotone" dataKey="income" name="收入(元)" stroke="#52c41a" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  )

  if (isMobile) {
    return (
      <div>
        <Title level={5}>经营概览</Title>
        <div className="mobile-stats-grid">
          <div className="stat-card">
            <div className="stat-value"><ShoppingCartOutlined /> {stats?.total_orders || 0}</div>
            <div className="stat-label">总订单</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#3f8600' }}><DollarOutlined /> ¥{stats?.total_income?.toFixed(2) || '0.00'}</div>
            <div className="stat-label">总收入</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#faad14' }}><ClockCircleOutlined /> {stats?.pending_orders || 0}</div>
            <div className="stat-label">待处理</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#eb2f96' }}><StarOutlined /> {stats?.avg_rating?.toFixed(1) || '0.0'}</div>
            <div className="stat-label">评分</div>
          </div>
        </div>
        {renderTrendChart()}
      </div>
    )
  }

  return (
    <div>
      <Title level={4}>经营概览</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title="总订单" value={stats?.total_orders || 0} prefix={<ShoppingCartOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="总收入" value={stats?.total_income || 0} prefix={<DollarOutlined />} valueStyle={{ color: '#3f8600' }} precision={2} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="待处理" value={stats?.pending_orders || 0} prefix={<ClockCircleOutlined />} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="评分" value={stats?.avg_rating || 0} prefix={<StarOutlined />} valueStyle={{ color: '#eb2f96' }} precision={1} suffix="分" />
          </Card>
        </Col>
      </Row>
      {renderTrendChart()}
    </div>
  )
}
