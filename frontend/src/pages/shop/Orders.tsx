
import { useState, useEffect } from 'react'
import { Card, Typography, Tabs, List, Empty, Button, Space, Tag, Spin, message } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { shopApi, OrderInfo } from '../../services/shop'

const { Title, Text } = Typography

export default function ShopOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [status, setStatus] = useState<string>('')

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const res = await shopApi.getShopOrders(status)
      setOrders(res.data)
    } catch (error) {
      console.error('获取订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [status])

  const handleAccept = async (id: number) => {
    try {
      await shopApi.acceptOrder(id)
      message.success('接单成功')
      fetchOrders()
    } catch (error) {
      console.error('接单失败', error)
    }
  }

  const handleReject = async (id: number) => {
    try {
      await shopApi.rejectOrder(id)
      message.success('拒单成功')
      fetchOrders()
    } catch (error) {
      console.error('拒单失败', error)
    }
  }

  const handleReady = async (id: number) => {
    try {
      await shopApi.orderReady(id)
      message.success('备餐完成')
      fetchOrders()
    } catch (error) {
      console.error('操作失败', error)
    }
  }

  const getStatusText = (status: string) => {
    const statusMap: Record<string, { text: string; color: string }> = {
      PENDING_PAYMENT: { text: '待支付', color: 'blue' },
      PENDING_ACCEPT: { text: '待接单', color: 'orange' },
      ACCEPTED: { text: '备餐中', color: 'cyan' },
      READY: { text: '待骑手取餐', color: 'purple' },
      DELIVERING: { text: '配送中', color: 'gold' },
      COMPLETED: { text: '已完成', color: 'green' },
      CANCELLED: { text: '已取消', color: 'default' },
    }
    return statusMap[status] || { text: status, color: 'default' }
  }

  const tabItems = [
    { key: '', label: '全部' },
    { key: 'PENDING_ACCEPT', label: '待接单' },
    { key: 'ACCEPTED', label: '备餐中' },
    { key: 'COMPLETED', label: '已完成' },
  ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Card>
      <Title level={4}>订单管理</Title>
      <Tabs
        activeKey={status}
        onChange={setStatus}
        items={tabItems}
      />

      {orders.length === 0 ? (
        <Empty description="暂无订单" style={{ marginTop: 50 }} />
      ) : (
        <List
          dataSource={orders}
          renderItem={(order) => {
            const statusInfo = getStatusText(order.status)
            return (
              <List.Item
                key={order.id}
                style={{ borderBottom: '1px solid #f0f0f0', padding: '16px 0' }}
                actions={
                  order.status === 'PENDING_ACCEPT'
                    ? [
                        <Button key="reject" danger icon={<CloseCircleOutlined />} onClick={() => handleReject(order.id)}>
                          拒单
                        </Button>,
                        <Button key="accept" type="primary" icon={<CheckCircleOutlined />} onClick={() => handleAccept(order.id)}>
                          接单
                        </Button>
                      ]
                    : order.status === 'ACCEPTED'
                    ? [
                        <Button key="ready" type="primary" icon={<ClockCircleOutlined />} onClick={() => handleReady(order.id)}>
                          备餐完成
                        </Button>
                      ]
                    : []
                }
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>订单号：{order.order_no}</Text>
                      <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text>
                        收货人：{order.address.contact_name} {order.address.contact_phone}
                        <br />
                        地址：{order.address.address}
                        <br />
                      </Text>
                      {order.items.map((item) => (
                        <Text key={item.id} type="secondary">
                          {item.product_name} × {item.quantity}
                          <br />
                        </Text>
                      ))}
                      <br />
                      <Text type="danger" strong>¥{order.total_amount.toFixed(2)}</Text>
                    </div>
                  }
                />
              </List.Item>
            )
          }}
        />
      )}
    </Card>
  )
}

