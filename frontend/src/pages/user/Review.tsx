
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Form, Rate, Input, Button, message, Spin, Upload, Image } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { reviewApi } from '../../services/review'
import { orderApi } from '../../services/order'
import { uploadApi } from '../../services/upload'
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
  const [uploadedImages, setUploadedImages] = useState<string[]>([])

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
        images: uploadedImages,
      })
      message.success('评价成功')
      navigate('/user/orders')
    } catch (error) {
      console.error('评价失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File) => {
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件')
      return false
    }
    const isLt5M = file.size / 1024 / 1024 < 5
    if (!isLt5M) {
      message.error('图片大小不能超过 5MB')
      return false
    }
    try {
      const res = await uploadApi.upload(file)
      setUploadedImages((prev) => [...prev, res.data.url])
      message.success('图片上传成功')
    } catch {
      message.error('图片上传失败')
    }
    return false
  }

  const handleRemove = (url: string) => {
    setUploadedImages((prev) => prev.filter((img) => img !== url))
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

            <Form.Item label="上传图片（选填，最多3张）">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {uploadedImages.map((url, index) => (
                  <div key={index} style={{ position: 'relative', width: 104, height: 104 }}>
                    <Image
                      src={url}
                      width={100}
                      height={100}
                      style={{ borderRadius: 8, objectFit: 'cover' }}
                    />
                    <Button
                      type="text"
                      danger
                      size="small"
                      style={{ position: 'absolute', top: 0, right: 0 }}
                      onClick={() => handleRemove(url)}
                    >
                      删除
                    </Button>
                  </div>
                ))}
                {uploadedImages.length < 3 && (
                  <Upload
                    accept="image/*"
                    showUploadList={false}
                    beforeUpload={handleUpload}
                  >
                    <div
                      style={{
                        width: 100,
                        height: 100,
                        border: '1px dashed #d9d9d9',
                        borderRadius: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                      }}
                    >
                      <PlusOutlined style={{ fontSize: 24 }} />
                    </div>
                  </Upload>
                )}
              </div>
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

