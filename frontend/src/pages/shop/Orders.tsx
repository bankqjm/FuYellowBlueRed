
import { useState, useEffect } from 'react'
import { Card, Typography, Tabs, List, Empty, Button, Space, Tag, Spin, message, Modal, Input } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { shopApi, OrderInfo } from '../../services/shop'

const { Title, Text } = Typography
const { TextArea } = Input

const rejectReasons = [
  '商品已售罄',
  '商家已打烊',
  '订单信息有误',
  '配送范围外',
  '其他原因',
]

export default function ShopOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [status, setStatus] = useState<string>('')
  const [rejectModalVisible, setRejectModalVisible] = useState(false)
  const [rejectingOrder, setRejectingOrder] = useState<OrderInfo | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const res = await shopApi.getShopOrders({ status: status || undefined })
      setOrders(res.data.items)
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

  const handleReject = async (order: OrderInfo) => {
    setRejectingOrder(order)
    setRejectReason('')
    setRejectModalVisible(true)
  }

  const confirmReject = async () => {
    if (!rejectReason.trim()) {
      message.warning('请选择或输入拒单原因')
      return
    }
    if (!rejectingOrder) {return}
    try {
      await shopApi.rejectOrder(rejectingOrder.id, rejectReason)
      message.success('拒单成功')
      setRejectModalVisible(false)
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
                      <Button key="reject" danger icon={<CloseCircleOutlined />} onClick={() => handleReject(order)}>
                          拒单
                      </Button>,
                      <Button key="accept" type="primary" icon={<CheckCircleOutlined />} onClick={() => handleAccept(order.id)}>
                          接单
                      </Button>,
                    ]
                    : order.status === 'ACCEPTED'
                      ? [
                        <Button key="ready" type="primary" icon={<ClockCircleOutlined />} onClick={() => handleReady(order.id)}>
                          备餐完成
                        </Button>,
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
                        收货人：{order.address_info?.contact_name} {order.address_info?.contact_phone}
                        <br />
                        地址：{order.address_info?.address || order.address}
                        <br />
                      </Text>
                      {order.items?.map((item) => (
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

      <Modal
        title="拒单原因"
        open={rejectModalVisible}
        onCancel={() => setRejectModalVisible(false)}
        onOk={confirmReject}
        okText="确认拒单"
        okButtonProps={{ danger: true }}
      >
        <div>
          <p style={{ marginBottom: 12 }}>请选择拒单原因：</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
            {rejectReasons.map((reason) => (
              <Button
                key={reason}
                type={rejectReason === reason ? 'primary' : 'default'}
                onClick={() => setRejectReason(reason)}
              >
                {reason}
              </Button>
            ))}
          </div>
          <Text type="secondary">如有其他原因，请在此说明：</Text>
          <TextArea
            rows={2}
            placeholder="选填"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            style={{ marginTop: 8 }}
          />
        </div>
      </Modal>
    </Card>
  )
}

