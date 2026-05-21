import { useState, useEffect } from 'react'
import { Card, Typography, Row, Col, Statistic, Table, Tag, Spin, Empty, Button } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { CheckCircleOutlined, ClockCircleOutlined, ShopOutlined } from '@ant-design/icons'
import api from '@/services/api'
import { useIsMobile } from '@/hooks/useIsMobile'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography

interface EarningsSummary {
  total_earnings: number
  settled_amount: number
  unsettled_amount: number
  order_count: number
}

interface EarningItem {
  id: number
  order_id: number
  gross_amount: number
  commission_rate: number
  commission_amount: number
  net_amount: number
  status: string
  created_at: string
}

export default function ShopEarnings() {
  const navigate = useNavigate()
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [hasShop, setHasShop] = useState<boolean | null>(null)
  const [summary, setSummary] = useState<EarningsSummary | null>(null)
  const [earnings, setEarnings] = useState<EarningItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)

  const fetchSummary = async () => {
    try {
      const res = await api.get('/shop/earnings/summary')
      setSummary(res.data)
      setHasShop(true)
    } catch (error: any) {
      if (error?.response?.data?.message?.includes('没有店铺')) {
        setHasShop(false)
      } else {
        console.error('获取收益汇总失败', error)
      }
    }
  }

  const fetchEarnings = async () => {
    try {
      setLoading(true)
      const res = await api.get('/shop/earnings/list', { params: { page, page_size: pageSize } })
      setEarnings(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch (error) {
      console.error('获取收益明细失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [])

  useEffect(() => {
    fetchEarnings()
  }, [page])

  const columns: ColumnsType<EarningItem> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '订单ID', dataIndex: 'order_id', width: 80 },
    { title: '总金额', dataIndex: 'gross_amount', width: 90, render: (v) => `¥${Number(v).toFixed(2)}` },
    { title: '佣金率', dataIndex: 'commission_rate', width: 80, render: (v) => `${(Number(v) * 100).toFixed(1)}%` },
    { title: '佣金', dataIndex: 'commission_amount', width: 80, render: (v) => `¥${Number(v).toFixed(2)}` },
    { title: '净收入', dataIndex: 'net_amount', width: 90, render: (v) => <Text type="success">¥{Number(v).toFixed(2)}</Text> },
    { title: '状态', dataIndex: 'status', width: 80, render: (v) => v === 'SETTLED' ? <Tag color="green">已结算</Tag> : <Tag color="orange">未结算</Tag> },
    { title: '时间', dataIndex: 'created_at', width: 160, render: (v) => v ? new Date(v).toLocaleString() : '-' },
  ]

  if (hasShop === false) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Empty
          image={<ShopOutlined style={{ fontSize: 48, color: '#1890ff' }} />}
          description={
            <div>
              <p style={{ color: '#8c8c8c' }}>欢迎入驻！创建店铺后即可查看收益</p>
              <Button type="primary" onClick={() => navigate('/shop/info')}>创建我的店铺</Button>
            </div>
          }
        />
      </div>
    )
  }

  if (isMobile) {
    return (
      <div>
        <Card>
          <Title level={5}>收益管理</Title>
        </Card>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>¥{(summary?.total_earnings || 0).toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#999' }}>总收益</div>
          </Card>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>¥{(summary?.settled_amount || 0).toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#999' }}>已结算</div>
          </Card>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#faad14' }}>¥{(summary?.unsettled_amount || 0).toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#999' }}>未结算</div>
          </Card>
          <Card style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 700 }}>{summary?.order_count || 0}</div>
            <div style={{ fontSize: 12, color: '#999' }}>订单数</div>
          </Card>
        </div>
        <Card style={{ marginTop: 8 }}>
          <Title level={5}>收益明细</Title>
          {loading ? <Spin /> : earnings.map((item) => (
            <Card key={item.id} size="small" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>订单 #{item.order_id}</span>
                {item.status === 'SETTLED' ? <Tag color="green">已结算</Tag> : <Tag color="orange">未结算</Tag>}
              </div>
              <div>净收入: <Text type="success">¥{Number(item.net_amount).toFixed(2)}</Text></div>
              <div style={{ fontSize: 12, color: '#999' }}>{item.created_at ? new Date(item.created_at).toLocaleString() : '-'}</div>
            </Card>
          ))}
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4}>收益管理</Title>
      </Card>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={6}>
          <Card><Statistic title="总收益" value={summary?.total_earnings || 0} prefix="¥" valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="已结算" value={summary?.settled_amount || 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#1890ff' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="未结算" value={summary?.unsettled_amount || 0} prefix={<ClockCircleOutlined />} valueStyle={{ color: '#faad14' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="订单数" value={summary?.order_count || 0} /></Card>
        </Col>
      </Row>
      <Card style={{ marginTop: 16 }}>
        <Title level={5}>收益明细</Title>
        <Table
          columns={columns}
          dataSource={earnings}
          rowKey="id"
          loading={loading}
          pagination={{ current: page, pageSize, total, onChange: setPage }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  )
}
