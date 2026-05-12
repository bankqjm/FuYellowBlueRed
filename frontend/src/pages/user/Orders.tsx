
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Tabs, List, Empty, Typography, Button, Space, Spin, message, Tag, Image, Modal } from 'antd'
import { orderApi, OrderInfo } from '../../services/order'

const { Title, Text } = Typography

export default function Orders() {
  const navigate = useNavigate()
  const params = useParams() as { id?: string; pay?: string }
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState&lt;OrderInfo[]&gt;([])
  const [status, setStatus] = useState&lt;string&gt;('')
  const [payModalVisible, setPayModalVisible] = useState(false)
  const [payingOrder, setPayingOrder] = useState&lt;OrderInfo | null&gt;(null)

  const fetchOrders = async () =&gt; {
    try {
      setLoading(true)
      const res = await orderApi.getOrders({ status: status || undefined })
      setOrders(res.data)
    } catch (error) {
      console.error('获取订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() =&gt; {
    fetchOrders()
  }, [status])

  useEffect(() =&gt; {
    if (params.id &amp;&amp; params.pay) {
      loadOrderAndShowPay(params.id)
    }
  }, [params.id, params.pay])

  const loadOrderAndShowPay = async (orderId: string) =&gt; {
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

  const handlePay = async (order: OrderInfo) =&gt; {
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

  const handleConfirmReceive = async (order: OrderInfo) =&gt; {
    try {
      setLoading(true)
      await orderApi.confirmReceive(order.id)
      message.success('确认收货成功')
      fetchOrders()
    } catch (error) {
      console.error('确认收货失败', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusText = (status: string) =&gt; {
    const statusMap: Record&lt;string, { text: string; color: string }&gt; = {
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

  const tabItems = [
    { key: '', label: '全部' },
    { key: 'PENDING_PAYMENT', label: '待支付' },
    { key: 'PENDING_ACCEPT', label: '待接单' },
    { key: 'DELIVERING', label: '配送中' },
    { key: 'COMPLETED', label: '已完成' },
  ]

  if (loading) {
    return (
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  return (
    &lt;div&gt;
      &lt;Card&gt;
        &lt;Title level={4}&gt;我的订单&lt;/Title&gt;
      &lt;/Card&gt;

      &lt;Card style={{ marginTop: 16 }}&gt;
        &lt;Tabs
          activeKey={status}
          onChange={setStatus}
          items={tabItems}
        /&gt;

        {orders.length === 0 ? (
          &lt;Empty description="暂无订单" style={{ marginTop: 50 }} /&gt;
        ) : (
          &lt;List
            dataSource={orders}
            renderItem={(order) =&gt; {
              const statusInfo = getStatusText(order.status)
              return (
                &lt;List.Item
                  key={order.id}
                  style={{ borderBottom: '1px solid #f0f0f0', padding: '16px 0' }}
                  actions={
                    order.status === 'PENDING_PAYMENT'
                      ? [
                          &lt;Button type="primary" key="pay" onClick={() =&gt; {
                            setPayingOrder(order)
                            setPayModalVisible(true)
                          }}&gt;
                            立即支付
                          &lt;/Button&gt;
                        ]
                      : order.status === 'DELIVERING'
                      ? [
                          &lt;Button type="primary" key="confirm" onClick={() =&gt; handleConfirmReceive(order)}&gt;
                            确认收货
                          &lt;/Button&gt;
                        ]
                      : []
                  }
                &gt;
                  &lt;List.Item.Meta
                    avatar={
                      order.shop_image ? (
                        &lt;Image src={order.shop_image} alt="" width={60} height={60} /&gt;
                      ) : (
                        &lt;div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}&gt;
                          &lt;span style={{ color: '#999' }}&gt;店铺&lt;/span&gt;
                        &lt;/div&gt;
                      )
                    }
                    title={
                      &lt;Space&gt;
                        &lt;Text strong&gt;{order.shop_name}&lt;/Text&gt;
                        &lt;Tag color={statusInfo.color}&gt;{statusInfo.text}&lt;/Tag&gt;
                      &lt;/Space&gt;
                    }
                    description={
                      &lt;div&gt;
                        &lt;Text type="secondary"&gt;订单号：{order.order_no}&lt;/Text&gt;
                        &lt;br /&gt;
                        {order.items.map((item) =&gt; (
                          &lt;Text key={item.id} type="secondary"&gt;
                            {item.product_name} × {item.quantity}
                            &lt;br /&gt;
                          &lt;/Text&gt;
                        ))}
                        &lt;br /&gt;
                        &lt;Text type="danger" strong&gt;¥{order.total_amount.toFixed(2)}&lt;/Text&gt;
                      &lt;/div&gt;
                    }
                  /&gt;
                &lt;/List.Item&gt;
              )
            }}
          /&gt;
        )}
      &lt;/Card&gt;

      &lt;Modal
        title="订单支付"
        open={payModalVisible}
        onCancel={() =&gt; setPayModalVisible(false)}
        footer={null}
      &gt;
        {payingOrder &amp;&amp; (
          &lt;div&gt;
            &lt;Text&gt;订单号：{payingOrder.order_no}&lt;/Text&gt;
            &lt;br /&gt;
            &lt;br /&gt;
            &lt;Text strong&gt;支付金额：&lt;/Text&gt;
            &lt;Text type="danger" strong style={{ fontSize: 24 }}&gt;¥{payingOrder.total_amount.toFixed(2)}&lt;/Text&gt;
            &lt;br /&gt;
            &lt;br /&gt;
            &lt;Button
              type="primary"
              size="large"
              style={{ width: '100%' }}
              onClick={() =&gt; handlePay(payingOrder)}
              loading={loading}
            &gt;
              立即支付
            &lt;/Button&gt;
          &lt;/div&gt;
        )}
      &lt;/Modal&gt;
    &lt;/div&gt;
  )
}

