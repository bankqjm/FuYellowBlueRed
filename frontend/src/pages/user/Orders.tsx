
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Tabs, List, Empty, Typography, Button, Space, Spin, message, Tag, Image, Modal, Timeline } from 'antd'
import { RedoOutlined } from '@ant-design/icons'
import { orderApi, cartApi } from '../../services/order'
import type { OrderInfo } from '../../services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'
import CountdownTimer, { formatTime } from '@/components/CountdownTimer'

const { Title, Text } = Typography

const POLLING_INTERVAL = 5000

export default function Orders() {
  const navigate = useNavigate()
  const params = useParams() as { id?: string; pay?: string }
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [status, setStatus] = useState<string>('')
  const [payModalVisible, setPayModalVisible] = useState(false)
  const [payingOrder, setPayingOrder] = useState<OrderInfo | null>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [detailOrder, setDetailOrder] = useState<OrderInfo | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchOrders = async () => {
    try {
      const res = await orderApi.listOrders({ status: status || undefined })
      setOrders(res.data.items)
    } catch (error) {
      console.error('获取订单失败', error)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [status])

  useEffect(() => {
    if (params.id && params.pay) {
      loadOrderAndShowPay(params.id)
    }
  }, [params.id, params.pay])

  useEffect(() => {
    const hasActiveOrders = orders.some((order) =>
      ['PENDING_PAYMENT', 'PENDING_ACCEPT', 'ACCEPTED', 'READY', 'DELIVERING'].includes(order.status),
    )

    if (hasActiveOrders) {
      pollingRef.current = setInterval(() => {
        fetchOrders()
      }, POLLING_INTERVAL)
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [orders, status])

  const loadOrderAndShowPay = async (orderId: string) => {
    try {
      const res = await orderApi.getOrderDetail(parseInt(orderId))
      if (res.data.status === 'PENDING_PAYMENT') {
        setPayingOrder(res.data)
        setPayModalVisible(true)
      }
    } catch (error) {
      console.error('加载订单失败', error)
    }
  }

  const handlePay = async (order: OrderInfo) => {
    try {
      setLoading(true)
      await orderApi.payOrder(order.id)
      message.success('支付成功')
      setPayModalVisible(false)
      fetchOrders()
    } catch (error) {
      console.error('支付失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelOrder = async (order: OrderInfo) => {
    try {
      setLoading(true)
      await orderApi.cancelOrder(order.id)
      message.success('订单已取消')
      setPayModalVisible(false)
      fetchOrders()
    } catch (error) {
      console.error('取消订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  const getPaymentDeadline = (order: OrderInfo): Date => {
    const createdTime = order.created_at ? new Date(order.created_at).getTime() : Date.now()
    return new Date(createdTime + 15 * 60 * 1000)
  }

  const handleCountdownExpire = () => {
    message.warning('订单支付超时，已自动取消')
    setPayModalVisible(false)
    fetchOrders()
  }

  const handleConfirmReceive = async (order: OrderInfo) => {
    try {
      setLoading(true)
      await orderApi.confirmReceipt(order.id)
      message.success('确认收货成功')
      fetchOrders()
    } catch (error) {
      console.error('确认收货失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReorder = async (order: OrderInfo) => {
    try {
      if (!order.items || order.items.length === 0) {
        message.warning('该订单无商品信息')
        return
      }
      for (const item of order.items) {
        await cartApi.addToCart({
          shop_id: order.shop_id,
          product_id: item.product_id,
          quantity: item.quantity,
        })
      }
      message.success('商品已加入购物车')
      navigate('/user/cart')
    } catch (error) {
      console.error('再来一单失败', error)
      message.error('操作失败，请重试')
    }
  }

  const showOrderDetail = async (order: OrderInfo) => {
    try {
      const res = await orderApi.getOrderDetail(order.id)
      setDetailOrder(res.data)
      setDetailModalVisible(true)
    } catch (error) {
      console.error('获取订单详情失败', error)
    }
  }

  const getStatusText = (status: string) => {
    const statusMap: Record<string, { text: string; color: string }> = {
      PENDING_PAYMENT: { text: '待支付', color: 'blue' },
      PENDING_ACCEPT: { text: '待商家接单', color: 'orange' },
      ACCEPTED: { text: '商家已接单', color: 'cyan' },
      READY: { text: '待骑手取餐', color: 'purple' },
      DELIVERING: { text: '配送中', color: 'gold' },
      COMPLETED: { text: '已完成', color: 'green' },
      CANCELLED: { text: '已取消', color: 'default' },
    }
    return statusMap[status] || { text: status, color: 'default' }
  }

  const getOrderTimeline = (order: OrderInfo) => {
    const items = [
      { color: 'green', children: `订单创建 - ${order.created_at ? new Date(order.created_at).toLocaleString() : ''}` },
    ]

    if (order.status !== 'PENDING_PAYMENT' && order.status !== 'CANCELLED') {
      items.push({ color: 'blue', children: '支付成功' })
    }

    if (['ACCEPTED', 'READY', 'DELIVERING', 'COMPLETED'].includes(order.status)) {
      items.push({ color: 'cyan', children: '商家已接单' })
    }

    if (['READY', 'DELIVERING', 'COMPLETED'].includes(order.status)) {
      items.push({ color: 'purple', children: '餐品已备好' })
    }

    if (['DELIVERING', 'COMPLETED'].includes(order.status)) {
      items.push({ color: 'gold', children: '骑手配送中' })
    }

    if (order.status === 'COMPLETED') {
      items.push({ color: 'green', children: '订单已完成' })
    }

    if (order.status === 'CANCELLED') {
      items.push({ color: 'red', children: '订单已取消' })
    }

    return items
  }

  const tabItems = [
    { key: '', label: '全部' },
    { key: 'PENDING_PAYMENT', label: '待支付' },
    { key: 'PENDING_ACCEPT', label: '待接单' },
    { key: 'ACCEPTED', label: '备餐中' },
    { key: 'DELIVERING', label: '配送中' },
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
    <div>
      <Card>
        <Title level={4}>我的订单</Title>
      </Card>

      <Card style={{ marginTop: isMobile ? 8 : 16 }}>
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
                  style={{ borderBottom: '1px solid #f0f0f0', padding: isMobile ? '12px 0' : '16px 0' }}
                  actions={
                    isMobile ? undefined : (
                      order.status === 'PENDING_PAYMENT'
                        ? [
                          <Button key="pay" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                          <Button key="cancel" danger onClick={() => Modal.confirm({ title: '确认取消', content: '确定要取消该订单吗？', onOk: () => handleCancelOrder(order) })}>取消订单</Button>,
                          <Button type="primary" key="paybtn" onClick={() => {
                            setPayingOrder(order)
                            setPayModalVisible(true)
                          }}>
                              立即支付
                          </Button>,
                        ]
                        : order.status === 'PENDING_ACCEPT'
                          ? [
                            <Button key="detail" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                            <Button key="cancel" danger onClick={() => Modal.confirm({ title: '确认取消', content: '确定要取消该订单吗？', onOk: () => handleCancelOrder(order) })}>取消订单</Button>,
                          ]
                          : order.status === 'DELIVERING'
                            ? [
                              <Button key="detail" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                              <Button type="primary" key="confirm" onClick={() => handleConfirmReceive(order)}>
                              确认收货
                              </Button>,
                            ]
                            : order.status === 'COMPLETED'
                              ? [
                                <Button key="detail" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                                <Button key="reorder" icon={<RedoOutlined />} onClick={() => handleReorder(order)}>
                              再来一单
                                </Button>,
                                <Button key="review" onClick={() => navigate(`/user/review/${order.id}`)}>
                              去评价
                                </Button>,
                              ]
                              : order.status === 'CANCELLED'
                                ? [
                                  <Button key="detail" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                                  <Button key="reorder" icon={<RedoOutlined />} onClick={() => handleReorder(order)}>
                              再来一单
                                  </Button>,
                                ]
                                : [
                                  <Button key="detail" onClick={() => showOrderDetail(order)}>查看详情</Button>,
                                ]
                    )
                  }
                >
                  <List.Item.Meta
                    avatar={
                      order.shop_image ? (
                        <Image src={order.shop_image} alt="" width={isMobile ? 48 : 60} height={isMobile ? 48 : 60} style={{ borderRadius: 6 }} />
                      ) : (
                        <div style={{
                          width: isMobile ? 48 : 60, height: isMobile ? 48 : 60, background: '#f0f0f0',
                          borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          <span style={{ color: '#999', fontSize: 12 }}>店铺</span>
                        </div>
                      )
                    }
                    title={
                      <Space>
                        <Text strong>{order.shop_name}</Text>
                        <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>订单号：{order.order_no}</Text>
                        <br />
                        {order.items && order.items.slice(0, 2).map((item) => (
                          <Text key={item.id} type="secondary" style={{ fontSize: 12 }}>
                            {item.product_name} × {item.quantity}
                            <br />
                          </Text>
                        ))}
                        {order.items && order.items.length > 2 && (
                          <Text type="secondary" style={{ fontSize: 12 }}>...等{order.items.length}件商品</Text>
                        )}
                        <br />
                        <Text type="danger" strong>¥{order.total_amount.toFixed(2)}</Text>
                        {isMobile && (
                          <div style={{ marginTop: 6 }}>
                            <Space size="small" wrap>
                              <Button size="small" onClick={() => showOrderDetail(order)}>详情</Button>
                              {order.status === 'PENDING_PAYMENT' && (
                                <Button type="primary" size="small" onClick={() => {
                                  setPayingOrder(order)
                                  setPayModalVisible(true)
                                }}>支付</Button>
                              )}
                              {(order.status === 'PENDING_PAYMENT' || order.status === 'PENDING_ACCEPT') && (
                                <Button size="small" danger onClick={() => Modal.confirm({ title: '确认取消', content: '确定要取消该订单吗？', onOk: () => handleCancelOrder(order) })}>取消订单</Button>
                              )}
                              {order.status === 'DELIVERING' && (
                                <Button type="primary" size="small" onClick={() => handleConfirmReceive(order)}>确认收货</Button>
                              )}
                              {(order.status === 'COMPLETED' || order.status === 'CANCELLED') && (
                                <Button size="small" icon={<RedoOutlined />} onClick={() => handleReorder(order)}>再来一单</Button>
                              )}
                              {order.status === 'COMPLETED' && (
                                <Button size="small" onClick={() => navigate(`/user/review/${order.id}`)}>评价</Button>
                              )}
                            </Space>
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )
            }}
          />
        )}
      </Card>

      <Modal
        title="订单支付"
        open={payModalVisible}
        onCancel={() => setPayModalVisible(false)}
        footer={null}
        width={isMobile ? undefined : 400}
      >
        {payingOrder && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>剩余支付时间</Text>
              <div style={{ marginTop: 4 }}>
                <CountdownTimer
                  endTime={getPaymentDeadline(payingOrder)}
                  onExpire={handleCountdownExpire}
                  warningThreshold={300}
                />
              </div>
            </div>
            <Text>订单号：{payingOrder.order_no}</Text>
            <br />
            <br />
            <Text strong>支付金额：</Text>
            <Text type="danger" strong style={{ fontSize: 24 }}>¥{payingOrder.total_amount.toFixed(2)}</Text>
            <br />
            <br />
            <Space style={{ width: '100%' }} direction="vertical">
              <Button
                type="primary"
                size="large"
                style={{ width: '100%' }}
                onClick={() => handlePay(payingOrder)}
                loading={loading}
              >
                立即支付
              </Button>
              <Button
                danger
                size="large"
                style={{ width: '100%' }}
                onClick={() => Modal.confirm({
                  title: '确认取消',
                  content: '确定要取消该订单吗？',
                  onOk: () => handleCancelOrder(payingOrder),
                })}
              >
                取消订单
              </Button>
            </Space>
          </div>
        )}
      </Modal>

      <Modal
        title="订单详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={isMobile ? undefined : 500}
      >
        {detailOrder && (
          <div>
            <p>
              <Text strong>订单号：</Text>{detailOrder.order_no}
            </p>
            <p>
              <Text strong>商家：</Text>{detailOrder.shop_name}
            </p>
            <p>
              <Text strong>配送地址：</Text>{detailOrder.address}
            </p>
            <p>
              <Text strong>联系电话：</Text>{detailOrder.phone}
            </p>
            {detailOrder.remark && (
              <p>
                <Text strong>备注：</Text>{detailOrder.remark}
              </p>
            )}
            <p>
              <Text strong>订单金额：</Text>¥{detailOrder.total_amount.toFixed(2)}
            </p>
            <p>
              <Text strong>配送费：</Text>¥{detailOrder.delivery_fee.toFixed(2)}
            </p>
            {detailOrder.items && detailOrder.items.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>商品明细：</Text>
                <ul>
                  {detailOrder.items.map((item) => (
                    <li key={item.id}>
                      {item.product_name} × {item.quantity} - ¥{(item.price * item.quantity).toFixed(2)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div style={{ marginTop: 24 }}>
              <Text strong>订单状态：</Text>
              <div style={{ marginTop: 8 }}>
                <Timeline items={getOrderTimeline(detailOrder)} />
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
