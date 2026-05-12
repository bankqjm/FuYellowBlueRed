
import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Image, Spin, Descriptions, Tag } from 'antd'
import { ShopOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons'
import { shopApi, ShopInfo as ShopInfoType } from '../../services/shop'

const { TextArea } = Input

export default function ShopInfo() {
  const [shop, setShop] = useState<ShopInfoType | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [form] = Form.useForm()

  const fetchShop = async () => {
    try {
      setLoading(true)
      const res = await shopApi.getMyShop()
      setShop(res.data)
      form.setFieldsValue(res.data)
    } catch (error) {
      console.error('获取店铺信息失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShop()
  }, [])

  const handleApply = async (values: any) => {
    try {
      const res = await shopApi.apply(values)
      setShop(res.data)
      message.success('申请成功，等待审核')
      setEditing(false)
    } catch (error) {
      console.error('申请店铺失败:', error)
    }
  }

  const handleUpdate = async (values: any) => {
    try {
      const res = await shopApi.updateMyShop(values)
      setShop(res.data)
      message.success('更新成功')
      setEditing(false)
    } catch (error) {
      console.error('更新店铺失败:', error)
    }
  }

  const getStatusText = (status: number) => {
    switch (status) {
      case 0:
        return <Tag color="orange">待审核</Tag>
      case 1:
        return <Tag color="green">已通过</Tag>
      case 2:
        return <Tag color="blue">休息中</Tag>
      case -1:
        return <Tag color="red">已拒绝</Tag>
      default:
        return <Tag>未知</Tag>
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!shop) {
    return (
      <Card title="申请店铺">
        <Form form={form} onFinish={handleApply} layout="vertical">
          <Form.Item
            label="店铺名称"
            name="name"
            rules={[{ required: true, message: '请输入店铺名称' }]}
          >
            <Input placeholder="请输入店铺名称" />
          </Form.Item>
          <Form.Item label="店铺Logo" name="logo">
            <Input placeholder="请输入Logo链接" />
          </Form.Item>
          <Form.Item
            label="店铺地址"
            name="address"
            rules={[{ required: true, message: '请输入店铺地址' }]}
          >
            <Input placeholder="请输入店铺地址" />
          </Form.Item>
          <Form.Item label="营业时间" name="business_hours">
            <Input placeholder="例如：09:00 - 22:00" />
          </Form.Item>
          <Form.Item label="店铺公告" name="notice">
            <TextArea rows={4} placeholder="请输入店铺公告" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<ShopOutlined />}>
              提交申请
            </Button>
          </Form.Item>
        </Form>
      </Card>
    )
  }

  return (
    <Card
      title="店铺信息"
      extra={
        editing ? (
          <Button type="primary" icon={<SaveOutlined />} onClick={() => form.submit()}>
            保存
          </Button>
        ) : (
          <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>
            编辑
          </Button>
        )
      }
    >
      {editing ? (
        <Form form={form} onFinish={handleUpdate} layout="vertical">
          <Form.Item label="店铺名称" name="name">
            <Input />
          </Form.Item>
          <Form.Item label="店铺Logo" name="logo">
            <Input />
          </Form.Item>
          <Form.Item label="店铺地址" name="address">
            <Input />
          </Form.Item>
          <Form.Item label="营业时间" name="business_hours">
            <Input />
          </Form.Item>
          <Form.Item label="店铺公告" name="notice">
            <TextArea rows={4} />
          </Form.Item>
        </Form>
      ) : (
        <Descriptions column={1}>
          <Descriptions.Item label="店铺状态">{getStatusText(shop.status)}</Descriptions.Item>
          <Descriptions.Item label="店铺名称">{shop.name}</Descriptions.Item>
          <Descriptions.Item label="店铺Logo">
            {shop.logo ? <Image src={shop.logo} width={100} /> : '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label="店铺地址">{shop.address}</Descriptions.Item>
          <Descriptions.Item label="营业时间">{shop.business_hours || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="店铺公告">{shop.notice || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="店铺评分">{shop.rating} 分</Descriptions.Item>
        </Descriptions>
      )}
    </Card>
  )
}

