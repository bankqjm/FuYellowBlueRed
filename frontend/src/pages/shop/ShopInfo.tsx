
import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Image, Spin, Descriptions, Tag } from 'antd'
import { ShopOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons'
import { shopApi, ShopInfo as ShopInfoType } from '../../services/shop'

const { TextArea } = Input

export default function ShopInfo() {
  const [shop, setShop] = useState&lt;ShopInfoType | null&gt;(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [form] = Form.useForm()

  const fetchShop = async () =&gt; {
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

  useEffect(() =&gt; {
    fetchShop()
  }, [])

  const handleApply = async (values: any) =&gt; {
    try {
      const res = await shopApi.apply(values)
      setShop(res.data)
      message.success('申请成功，等待审核')
      setEditing(false)
    } catch (error) {
      console.error('申请店铺失败:', error)
    }
  }

  const handleUpdate = async (values: any) =&gt; {
    try {
      const res = await shopApi.updateMyShop(values)
      setShop(res.data)
      message.success('更新成功')
      setEditing(false)
    } catch (error) {
      console.error('更新店铺失败:', error)
    }
  }

  const getStatusText = (status: number) =&gt; {
    switch (status) {
      case 0:
        return &lt;Tag color="orange"&gt;待审核&lt;/Tag&gt;
      case 1:
        return &lt;Tag color="green"&gt;已通过&lt;/Tag&gt;
      case 2:
        return &lt;Tag color="blue"&gt;休息中&lt;/Tag&gt;
      case -1:
        return &lt;Tag color="red"&gt;已拒绝&lt;/Tag&gt;
      default:
        return &lt;Tag&gt;未知&lt;/Tag&gt;
    }
  }

  if (loading) {
    return (
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  if (!shop) {
    return (
      &lt;Card title="申请店铺"&gt;
        &lt;Form form={form} onFinish={handleApply} layout="vertical"&gt;
          &lt;Form.Item
            label="店铺名称"
            name="name"
            rules={[{ required: true, message: '请输入店铺名称' }]}
          &gt;
            &lt;Input placeholder="请输入店铺名称" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="店铺Logo" name="logo"&gt;
            &lt;Input placeholder="请输入Logo链接" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item
            label="店铺地址"
            name="address"
            rules={[{ required: true, message: '请输入店铺地址' }]}
          &gt;
            &lt;Input placeholder="请输入店铺地址" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="营业时间" name="business_hours"&gt;
            &lt;Input placeholder="例如：09:00 - 22:00" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="店铺公告" name="notice"&gt;
            &lt;TextArea rows={4} placeholder="请输入店铺公告" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item&gt;
            &lt;Button type="primary" htmlType="submit" icon={&lt;ShopOutlined /&gt;}&gt;
              提交申请
            &lt;/Button&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;
      &lt;/Card&gt;
    )
  }

  return (
    &lt;Card
      title="店铺信息"
      extra={
        editing ? (
          &lt;Button type="primary" icon={&lt;SaveOutlined /&gt;} onClick={() =&gt; form.submit()}&gt;
            保存
          &lt;/Button&gt;
        ) : (
          &lt;Button icon={&lt;EditOutlined /&gt;} onClick={() =&gt; setEditing(true)}&gt;
            编辑
          &lt;/Button&gt;
        )
      }
    &gt;
      {editing ? (
        &lt;Form form={form} onFinish={handleUpdate} layout="vertical"&gt;
          &lt;Form.Item label="店铺名称" name="name"&gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="店铺Logo" name="logo"&gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="店铺地址" name="address"&gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="营业时间" name="business_hours"&gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="店铺公告" name="notice"&gt;
            &lt;TextArea rows={4} /&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;
      ) : (
        &lt;Descriptions column={1}&gt;
          &lt;Descriptions.Item label="店铺状态"&gt;{getStatusText(shop.status)}&lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="店铺名称"&gt;{shop.name}&lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="店铺Logo"&gt;
            {shop.logo ? &lt;Image src={shop.logo} width={100} /&gt; : '未设置'}
          &lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="店铺地址"&gt;{shop.address}&lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="营业时间"&gt;{shop.business_hours || '未设置'}&lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="店铺公告"&gt;{shop.notice || '未设置'}&lt;/Descriptions.Item&gt;
          &lt;Descriptions.Item label="店铺评分"&gt;{shop.rating} 分&lt;/Descriptions.Item&gt;
        &lt;/Descriptions&gt;
      )}
    &lt;/Card&gt;
  )
}

