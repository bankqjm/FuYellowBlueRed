
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Typography, List, Button, Space, Image, Empty, Spin, message, Modal, Form, Select, Input } from 'antd'
import { MinusOutlined, PlusOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { cartApi, CartItemInfo, orderApi } from '../../services/order'
import { addressApi, AddressInfo } from '../../services/address'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

export default function Cart() {
  const navigate = useNavigate()
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [cart, setCart] = useState<CartItemInfo[]>([])
  const [addresses, setAddresses] = useState<AddressInfo[]>([])
  const [checkoutModalVisible, setCheckoutModalVisible] = useState(false)
  const [selectedAddress, setSelectedAddress] = useState<number | undefined>()
  const [remark, setRemark] = useState('')
  const [form] = Form.useForm()

  const fetchCart = async () => {
    try {
      setLoading(true)
      const res = await cartApi.getCart()
      setCart(res.data)
    } catch (error) {
      console.error('获取购物车失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAddresses = async () => {
    try {
      const res = await addressApi.getAddresses()
      setAddresses(res.data)
      if (res.data.length > 0) {
        const defaultAddr = res.data.find(a => a.is_default === 1)
        setSelectedAddress(defaultAddr?.id || res.data[0].id)
      }
    } catch (error) {
      console.error('获取地址列表失败', error)
    }
  }

  useEffect(() => {
    fetchCart()
    fetchAddresses()
  }, [])

  const updateCartItem = async (item: CartItemInfo, quantity: number) => {
    try {
      if (quantity <= 0) {
        await cartApi.deleteCartItem(item.id)
      } else {
        await cartApi.updateCartItem(item.id, { quantity })
      }
      message.success('购物车已更新')
      fetchCart()
    } catch (error) {
      console.error('更新购物车失败', error)
    }
  }

  const deleteCartItem = async (item: CartItemInfo) => {
    try {
      await cartApi.deleteCartItem(item.id)
      message.success('已删除')
      fetchCart()
    } catch (error) {
      console.error('删除购物车项失败', error)
    }
  }

  const handleCheckout = async () => {
    if (!selectedAddress) {
      message.error('请选择收货地址')
      return
    }

    if (cart.length === 0) {
      message.error('购物车为空')
      return
    }

    const shopId = cart[0].shop_id
    try {
      const res = await orderApi.createOrder({
        address_id: selectedAddress,
        shop_id: shopId,
        remark: remark,
      })
      message.success('订单创建成功')
      setCheckoutModalVisible(false)
      navigate(`/user/orders/${res.data.id}/pay`)
    } catch (error) {
      console.error('创建订单失败', error)
    }
  }

  const getCartTotal = () => {
    return {
      quantity: cart.reduce((sum, item) => sum + item.quantity, 0),
      price: cart.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0),
    }
  }

  const cartTotal = getCartTotal()

  const groupedCart = cart.reduce((acc, item) => {
    if (!acc[item.shop_id]) {
      acc[item.shop_id] = []
    }
    acc[item.shop_id].push(item)
    return acc
  }, {} as Record<number, CartItemInfo[]>)

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (cart.length === 0) {
    return (
      <Card>
        <Empty description="购物车为空" />
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Button type="primary" onClick={() => navigate('/user/home')}>
            去逛一逛
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4}>购物车</Title>
      </Card>

      {Object.entries(groupedCart).map(([shopId, items]) => (
        <Card key={shopId} style={{ marginTop: isMobile ? 8 : 16 }} title={items[0].shop_name}>
          <List
            dataSource={items}
            renderItem={(item) => (
              <List.Item
                actions={
                  isMobile ? undefined : [
                    <Space key="actions">
                      <Button
                        size="small"
                        shape="circle"
                        icon={<MinusOutlined />}
                        onClick={() => updateCartItem(item, item.quantity - 1)}
                      />
                      <Text>{item.quantity}</Text>
                      <Button
                        size="small"
                        shape="circle"
                        icon={<PlusOutlined />}
                        onClick={() => updateCartItem(item, item.quantity + 1)}
                      />
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => deleteCartItem(item)}
                      />
                    </Space>
                  ]
                }
              >
                <List.Item.Meta
                  avatar={
                    item.product_image ? (
                      <Image src={item.product_image} alt="" width={isMobile ? 48 : 60} height={isMobile ? 48 : 60} style={{ borderRadius: 6 }} />
                    ) : (
                      <div style={{
                        width: isMobile ? 48 : 60, height: isMobile ? 48 : 60, background: '#f0f0f0',
                        borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center'
                      }}>
                        <span style={{ color: '#999', fontSize: 12 }}>商品</span>
                      </div>
                    )
                  }
                  title={item.product_name}
                  description={
                    <div>
                      <Text type="danger">¥{item.product_price?.toFixed(2)}</Text>
                      {isMobile && (
                        <div style={{ marginTop: 4 }}>
                          <Space size="small">
                            <Button size="small" shape="circle" icon={<MinusOutlined />}
                              onClick={() => updateCartItem(item, item.quantity - 1)} />
                            <Text>{item.quantity}</Text>
                            <Button size="small" shape="circle" icon={<PlusOutlined />}
                              onClick={() => updateCartItem(item, item.quantity + 1)} />
                            <Button type="text" danger size="small" icon={<DeleteOutlined />}
                              onClick={() => deleteCartItem(item)} />
                          </Space>
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      ))}

      <Card
        style={{
          position: 'fixed',
          bottom: isMobile ? 56 : 0,
          left: 0,
          right: 0,
          boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
          zIndex: 99,
          borderRadius: 0,
        }}
      >
        <Space style={{ width: '100%', justifyContent: 'space-between', flexWrap: isMobile ? 'wrap' : 'nowrap' }}>
          <div>
            <Text>共</Text>
            <Text strong style={{ marginLeft: 4, marginRight: 4 }}>{cartTotal.quantity}</Text>
            <Text>件商品，合计：</Text>
            <Text type="danger" strong style={{ fontSize: 18 }}>¥{cartTotal.price.toFixed(2)}</Text>
          </div>
          <Space>
            {!isMobile && (
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/user/home')}>
                继续购物
              </Button>
            )}
            <Button type="primary" size="large" onClick={() => setCheckoutModalVisible(true)}>
              去结算
            </Button>
          </Space>
        </Space>
      </Card>

      <Modal
        title="确认订单"
        open={checkoutModalVisible}
        onCancel={() => setCheckoutModalVisible(false)}
        onOk={handleCheckout}
        width={isMobile ? undefined : 600}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="收货地址" name="address" rules={[{ required: true, message: '请选择收货地址' }]}>
            <Select
              placeholder="请选择收货地址"
              value={selectedAddress}
              onChange={setSelectedAddress}
              style={{ width: '100%' }}
            >
              {addresses.map(address => (
                <Option key={address.id} value={address.id}>
                  {address.contact_name} {address.contact_phone} - {address.address}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="订单备注">
            <TextArea
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              placeholder="请输入备注（选填）"
              rows={3}
            />
          </Form.Item>
        </Form>

        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">共{cartTotal.quantity}件商品，总计：</Text>
            <Text type="danger" strong style={{ fontSize: 24 }}>¥{cartTotal.price.toFixed(2)}</Text>
          </Space>
        </div>
      </Modal>
    </div>
  )
}
