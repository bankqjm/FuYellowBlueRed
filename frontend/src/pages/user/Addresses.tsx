
import { useState, useEffect } from 'react'
import { Card, Typography, List, Empty, Button, Space, Spin, message, Modal, Form, Input, Switch } from 'antd'
import { EnvironmentOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { addressApi, AddressInfo } from '../../services/address'

const { Text } = Typography

export default function Addresses() {
  const [loading, setLoading] = useState(false)
  const [addresses, setAddresses] = useState<AddressInfo[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingAddress, setEditingAddress] = useState<AddressInfo | null>(null)
  const [form] = Form.useForm()

  const fetchAddresses = async () => {
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

  useEffect(() => {
    fetchAddresses()
  }, [])

  const handleAdd = () => {
    setEditingAddress(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (address: AddressInfo) => {
    setEditingAddress(address)
    form.setFieldsValue(address)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await addressApi.deleteAddress(id)
      message.success('删除成功')
      fetchAddresses()
    } catch (error) {
      console.error('删除地址失败', error)
    }
  }

  const handleSubmit = async () => {
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
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Card
        title="收货地址"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增地址</Button>}
      >
        {addresses.length === 0 ? (
          <Empty
            description="暂无收货地址"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={addresses}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button key="edit" type="link" icon={<EditOutlined />} onClick={() => handleEdit(item)}>
                    编辑
                  </Button>,
                  <Button key="delete" type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(item.id)}>
                    删除
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={<EnvironmentOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                  title={
                    <Space>
                      <Text strong>{item.contact_name}</Text>
                      <Text>{item.contact_phone}</Text>
                      {item.is_default === 1 && <Text type="secondary">[默认地址]</Text>}
                    </Space>
                  }
                  description={
                    <Text type="secondary">{item.address}</Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Modal
        title={editingAddress ? '编辑地址' : '新增地址'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSubmit}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="收货人姓名"
            name="contact_name"
            rules={[{ required: true, message: '请输入收货人姓名' }]}
          >
            <Input placeholder="请输入收货人姓名" />
          </Form.Item>
          <Form.Item
            label="联系电话"
            name="contact_phone"
            rules={[{ required: true, message: '请输入联系电话' }]}
          >
            <Input placeholder="请输入联系电话" />
          </Form.Item>
          <Form.Item
            label="详细地址"
            name="address"
            rules={[{ required: true, message: '请输入详细地址' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入详细地址" />
          </Form.Item>
          <Form.Item label="设为默认地址" name="is_default" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

