
import { useState, useEffect } from 'react'
import { Card, Typography, List, Empty, Button, Space, Spin, message, Modal, Form, Input, Switch } from 'antd'
import { EnvironmentOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { addressApi, AddressInfo } from '../../services/address'

const { Title, Text } = Typography

export default function Addresses() {
  const [loading, setLoading] = useState(false)
  const [addresses, setAddresses] = useState&lt;AddressInfo[]&gt;([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingAddress, setEditingAddress] = useState&lt;AddressInfo | null&gt;(null)
  const [form] = Form.useForm()

  const fetchAddresses = async () =&gt; {
    try {
      setLoading(true)
      const res = await addressApi.getAddresses()
      setAddresses(res.data)
    } catch (error) {
      console.error('获取地址列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() =&gt; {
    fetchAddresses()
  }, [])

  const handleAdd = () =&gt; {
    setEditingAddress(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (address: AddressInfo) =&gt; {
    setEditingAddress(address)
    form.setFieldsValue(address)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) =&gt; {
    try {
      await addressApi.deleteAddress(id)
      message.success('删除成功')
      fetchAddresses()
    } catch (error) {
      console.error('删除地址失败', error)
    }
  }

  const handleSubmit = async () =&gt; {
    try {
      const values = await form.validateFields()
      if (editingAddress) {
        await addressApi.updateAddress(editingAddress.id, values)
        message.success('更新成功')
      } else {
        await addressApi.createAddress(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchAddresses()
    } catch (error) {
      console.error('保存地址失败', error)
    }
  }

  if (loading) {
    return (
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  return (
    &lt;div&gt;
      &lt;Card
        title="收货地址"
        extra={&lt;Button type="primary" icon={&lt;PlusOutlined /&gt;} onClick={handleAdd}&gt;新增地址&lt;/Button&gt;}
      &gt;
        {addresses.length === 0 ? (
          &lt;Empty
            description="暂无收货地址"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          /&gt;
        ) : (
          &lt;List
            dataSource={addresses}
            renderItem={(item) =&gt; (
              &lt;List.Item
                actions={[
                  &lt;Button key="edit" type="link" icon={&lt;EditOutlined /&gt;} onClick={() =&gt; handleEdit(item)}&gt;
                    编辑
                  &lt;/Button&gt;,
                  &lt;Button key="delete" type="link" danger icon={&lt;DeleteOutlined /&gt;} onClick={() =&gt; handleDelete(item.id)}&gt;
                    删除
                  &lt;/Button&gt;
                ]}
              &gt;
                &lt;List.Item.Meta
                  avatar={&lt;EnvironmentOutlined style={{ fontSize: 24, color: '#1890ff' }} /&gt;}
                  title={
                    &lt;Space&gt;
                      &lt;Text strong&gt;{item.contact_name}&lt;/Text&gt;
                      &lt;Text&gt;{item.contact_phone}&lt;/Text&gt;
                      {item.is_default === 1 &amp;&amp; &lt;Text type="primary"&gt;[默认地址]&lt;/Text&gt;}
                    &lt;/Space&gt;
                  }
                  description={
                    &lt;Text type="secondary"&gt;{item.address}&lt;/Text&gt;
                  }
                /&gt;
              &lt;/List.Item&gt;
            )}
          /&gt;
        )}
      &lt;/Card&gt;

      &lt;Modal
        title={editingAddress ? '编辑地址' : '新增地址'}
        open={modalVisible}
        onCancel={() =&gt; setModalVisible(false)}
        onOk={handleSubmit}
      &gt;
        &lt;Form form={form} layout="vertical"&gt;
          &lt;Form.Item
            label="收货人姓名"
            name="contact_name"
            rules={[{ required: true, message: '请输入收货人姓名' }]}
          &gt;
            &lt;Input placeholder="请输入收货人姓名" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item
            label="联系电话"
            name="contact_phone"
            rules={[{ required: true, message: '请输入联系电话' }]}
          &gt;
            &lt;Input placeholder="请输入联系电话" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item
            label="详细地址"
            name="address"
            rules={[{ required: true, message: '请输入详细地址' }]}
          &gt;
            &lt;Input.TextArea rows={3} placeholder="请输入详细地址" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="设为默认地址" name="is_default" valuePropName="checked"&gt;
            &lt;Switch /&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;
      &lt;/Modal&gt;
    &lt;/div&gt;
  )
}

