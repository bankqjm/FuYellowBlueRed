
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Form, Rate, Input, Button, message, Spin } from 'antd'
import { reviewApi } from '../../services/review'
import { orderApi } from '../../services/order'
import type { OrderInfo } from '../../services/shop'

const { Title, Text } = Typography
const { TextArea } = Input

export default function ReviewPage() {
  const navigate = useNavigate()
  const params = useParams() as { id: string }
  const [loading, setLoading] = useState(false)
  const [order, setOrder] = useState<OrderInfo | null>(null)
  const [form] = Form.useForm()
  const [shopRating, setShopRating] = useState(5)
  const [riderRating, setRiderRating] = useState(5)

  useEffect(() => {
    loadOrder()
  }, [])

  const loadOrder = async () => {
    try {
      setLoading(true)
      const res = await orderApi.getOrderDetail(parseInt(params.id))
      setOrder(res.data)
    } catch (error) {
      console.error('加载订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      await reviewApi.createReview({
        order_id: parseInt(params.id),
        shop_rating: shopRating,
        rider_rating: riderRating,
        content: values.content,
      })
      message.success('评价成功')
      navigate('/user/orders')
    } catch (error) {
      console.error('评价失败', error)
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

  return (
    <div>
      <Card>
        <Title level={4}>评价订单</Title>
      </Card>

      {order && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 24 }}>
            <Text type="secondary">订单号：{order.order_no}</Text>
            <br />
            <Text strong>{order.shop_name}</Text>
          </div>

          <Form form={form} layout="vertical">
            <Form.Item label="商家评分">
              <Rate value={shopRating} onChange={setShopRating} />
              <span style={{ marginLeft: 8 }}>{shopRating} 星</span>
            </Form.Item>

            {order.rider_id && (
              <Form.Item label="骑手评分">
                <Rate value={riderRating} onChange={setRiderRating} />
                <span style={{ marginLeft: 8 }}>{riderRating} 星</span>
              </Form.Item>
            )}

            <Form.Item label="评价内容（选填）" name="content">
              <TextArea rows={4} placeholder="分享您的用餐体验..." maxLength={500} showCount />
            </Form.Item>

            <Form.Item>
              <Button type="primary" size="large" onClick={handleSubmit} loading={loading} style={{ width: '100%' }}>
                提交评价
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}
    </div>
  )
}

