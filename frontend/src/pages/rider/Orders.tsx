
import { useState, useEffect } from 'react'
import { Card, Typography, Tabs, List, Empty, Button, Space, Tag, Spin, message, Modal } from 'antd'
import { InboxOutlined, CarOutlined } from '@ant-design/icons'
import { riderApi } from '../../services/rider'
import type { OrderInfo } from '../../services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

export default function RiderOrders() {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('available')
  const [availableOrders, setAvailableOrders] = useState<OrderInfo[]>([])
  const [activeOrders, setActiveOrders] = useState<OrderInfo[]>([])
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<OrderInfo | null>(null)
  const isMobile = useIsMobile()

  const fetchAvailableOrders = async () => {
    try {
      setLoading(true)
      const res = await riderApi.getAvailableOrders()
      setAvailableOrders(res.data.items)
    } catch (error) {
      console.error('获取待接单订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchActiveOrders = async () => {
    try {
      setLoading(true)
      const res = await riderApi.getActiveOrders()
      setActiveOrders(res.data.items)
    } catch (error) {
      console.error('获取进行中订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'available') {
      fetchAvailableOrders()
    } else {
      fetchActiveOrders()
    }
  }, [activeTab])

  const handleAccept = async (order: OrderInfo) => {
    try {
      setLoading(true)
      await riderApi.acceptOrder(order.id)
      message.success('接单成功')
      fetchAvailableOrders()
      fetchActiveOrders()
    } catch (error) {
      console.error('接单失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeliver = async (order: OrderInfo) => {
    try {
      setLoading(true)
      await riderApi.deliverOrder(order.id)
      message.success('确认送达成功，收入已到账')
      fetchActiveOrders()
    } catch (error) {
      console.error('确认送达失败', error)
    } finally {
      setLoading(false)
    }
  }

  const showOrderDetail = (order: OrderInfo) => {
    setSelectedOrder(order)
    setDetailModalVisible(true)
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  const renderOrderCard = (order: OrderInfo, type: 'available' | 'active') => (
    <div className="mobile-card" key={order.id}>
      <div className="card-row">
        <span className="label">订单号</span>
        <span className="value">{order.order_no}</span>
      </div>
      <div className="card-row">
        <span className="label">商家</span>
        <span className="value">{order.shop_name}</span>
      </div>
      <div className="card-row">
        <span className="label">配送地址</span>
        <span className="value" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{order.address}</span>
      </div>
      {type === 'available' ? (
        <div className="card-row">
          <span className="label">配送费</span>
          <span className="value" style={{ color: '#52c41a' }}>¥{order.delivery_fee.toFixed(2)}</span>
        </div>
      ) : (
        <div className="card-row">
          <span className="label">联系电话</span>
          <span className="value">{order.phone}</span>
        </div>
      )}
      <div className="card-actions">
        <Button size="small" onClick={() => showOrderDetail(order)}>详情</Button>
        {type === 'available' ? (
          <Button type="primary" size="small" onClick={() => handleAccept(order)}>接单</Button>
        ) : (
          <Button type="primary" size="small" onClick={() => handleDeliver(order)}>确认送达</Button>
        )}
      </div>
    </div>
  )

  const tabItemsConfig = [
    {
      key: 'available',
      label: <span><InboxOutlined /> 待接单</span>,
      children: isMobile ? (
        availableOrders.length === 0 ? (
          <Empty description="暂无待接单订单" style={{ marginTop: 30 }} />
        ) : (
          <div>{availableOrders.map(order => renderOrderCard(order, 'available'))}</div>
        )
      ) : (
        availableOrders.length === 0 ? (
          <Empty description="暂无待接单订单" style={{ marginTop: 50 }} />
        ) : (
          <List
            dataSource={availableOrders}
            renderItem={(order) => (
              <List.Item
                key={order.id}
                actions={[
                  <Button key="detail" onClick={() => showOrderDetail(order)}>
                    查看详情
                  </Button>,
                  <Button type="primary" key="accept" onClick={() => handleAccept(order)}>
                    立即接单
                  </Button>
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>订单号：{order.order_no}</Text>
                      <Tag color="gold">待接单</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text>
                        商家：{order.shop_name}
                        <br />
                        配送地址：{order.address}
                        <br />
                        配送费：<Text type="success">¥{order.delivery_fee.toFixed(2)}</Text>
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )
      ),
    },
    {
      key: 'active',
      label: <span><CarOutlined /> 进行中</span>,
      children: isMobile ? (
        activeOrders.length === 0 ? (
          <Empty description="暂无进行中订单" style={{ marginTop: 30 }} />
        ) : (
          <div>{activeOrders.map(order => renderOrderCard(order, 'active'))}</div>
        )
      ) : (
        activeOrders.length === 0 ? (
          <Empty description="暂无进行中订单" style={{ marginTop: 50 }} />
        ) : (
          <List
            dataSource={activeOrders}
            renderItem={(order) => (
              <List.Item
                key={order.id}
                actions={[
                  <Button key="detail" onClick={() => showOrderDetail(order)}>
                    查看详情
                  </Button>,
                  <Button type="primary" key="deliver" onClick={() => handleDeliver(order)}>
                    确认送达
                  </Button>
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>订单号：{order.order_no}</Text>
                      <Tag color="processing">配送中</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text>
                        商家：{order.shop_name}
                        <br />
                        配送地址：{order.address}
                        <br />
                        联系电话：{order.phone}
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )
      ),
    },
  ]

  return (
    <div>
      <Card>
        <Title level={4}>骑手接单</Title>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItemsConfig} />
      </Card>

      <Modal
        title="订单详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={isMobile ? undefined : undefined}
      >
        {selectedOrder && (
          <div>
            <p><Text strong>订单号：</Text>{selectedOrder.order_no}</p>
            <p><Text strong>商家名称：</Text>{selectedOrder.shop_name}</p>
            <p><Text strong>商家地址：</Text>-</p>
            <p><Text strong>收货人：</Text>{selectedOrder.phone}</p>
            <p><Text strong>配送地址：</Text>{selectedOrder.address}</p>
            <p><Text strong>订单金额：</Text>¥{selectedOrder.total_amount.toFixed(2)}</p>
            <p><Text strong>配送费：</Text><Text type="success">¥{selectedOrder.delivery_fee.toFixed(2)}</Text></p>
            {selectedOrder.items && selectedOrder.items.length > 0 && (
              <div>
                <Text strong>商品明细：</Text>
                <ul>
                  {selectedOrder.items.map((item) => (
                    <li key={item.id}>{item.product_name} × {item.quantity}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
