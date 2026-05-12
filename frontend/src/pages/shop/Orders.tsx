
import { useState, useEffect } from 'react'
import { Card, Typography, Tabs, List, Empty, Button, Space, Tag, Spin, message } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { shopApi, OrderInfo } from '../../services/shop'

const { Title, Text } = Typography

export default function ShopOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState&lt;OrderInfo[]&gt;([])
  const [status, setStatus] = useState&lt;string&gt;('')

  const fetchOrders = async () =&gt; {
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

  useEffect(() =&gt; {
    fetchOrders()
  }, [status])

  const handleAccept = async (id: number) =&gt; {
    try {
      await shopApi.acceptOrder(id)
      message.success('接单成功')
      fetchOrders()
    } catch (error) {
      console.error('接单失败', error)
    }
  }

  const handleReject = async (id: number) =&gt; {
    try {
      await shopApi.rejectOrder(id)
      message.success('拒单成功')
      fetchOrders()
    } catch (error) {
      console.error('拒单失败', error)
    }
  }

  const handleReady = async (id: number) =&gt; {
    try {
      await shopApi.orderReady(id)
      message.success('备餐完成')
      fetchOrders()
    } catch (error) {
      console.error('操作失败', error)
    }
  }

  const getStatusText = (status: string) =&gt; {
    const statusMap: Record&lt;string, { text: string; color: string }&gt; = {
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
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  return (
    &lt;Card&gt;
      &lt;Title level={4}&gt;订单管理&lt;/Title&gt;
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
                  order.status === 'PENDING_ACCEPT'
                    ? [
                        &lt;Button key="reject" danger icon={&lt;CloseCircleOutlined /&gt;} onClick={() =&gt; handleReject(order.id)}&gt;
                          拒单
                        &lt;/Button&gt;,
                        &lt;Button key="accept" type="primary" icon={&lt;CheckCircleOutlined /&gt;} onClick={() =&gt; handleAccept(order.id)}&gt;
                          接单
                        &lt;/Button&gt;
                      ]
                    : order.status === 'ACCEPTED'
                    ? [
                        &lt;Button key="ready" type="primary" icon={&lt;ClockCircleOutlined /&gt;} onClick={() =&gt; handleReady(order.id)}&gt;
                          备餐完成
                        &lt;/Button&gt;
                      ]
                    : []
                }
              &gt;
                &lt;List.Item.Meta
                  title={
                    &lt;Space&gt;
                      &lt;Text strong&gt;订单号：{order.order_no}&lt;/Text&gt;
                      &lt;Tag color={statusInfo.color}&gt;{statusInfo.text}&lt;/Tag&gt;
                    &lt;/Space&gt;
                  }
                  description={
                    &lt;div&gt;
                      &lt;Text&gt;
                        收货人：{order.address.contact_name} {order.address.contact_phone}
                        &lt;br /&gt;
                        地址：{order.address.address}
                        &lt;br /&gt;
                      &lt;/Text&gt;
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
  )
}

