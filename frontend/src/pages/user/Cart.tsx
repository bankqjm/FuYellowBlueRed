
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Typography, List, Button, Space, Image, Empty, Spin, message, Modal, Form, Select, Input, Radio } from 'antd'
import { MinusOutlined, PlusOutlined, DeleteOutlined, ShoppingOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { cartApi, CartItemInfo, orderApi } from '../../services/order'
import { addressApi, AddressInfo } from '../../services/address'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

export default function Cart() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [cart, setCart] = useState&lt;CartItemInfo[]&gt;([])
  const [addresses, setAddresses] = useState&lt;AddressInfo[]&gt;([])
  const [checkoutModalVisible, setCheckoutModalVisible] = useState(false)
  const [selectedAddress, setSelectedAddress] = useState&lt;number | undefined&gt;()
  const [remark, setRemark] = useState('')
  const [form] = Form.useForm()

  const fetchCart = async () =&gt; {
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

  const fetchAddresses = async () =&gt; {
    try {
      const res = await addressApi.getAddresses()
      setAddresses(res.data)
      if (res.data.length &gt; 0) {
        const defaultAddr = res.data.find(a =&gt; a.is_default === 1)
        setSelectedAddress(defaultAddr?.id || res.data[0].id)
      }
    } catch (error) {
      console.error('获取地址列表失败', error)
    }
  }

  useEffect(() =&gt; {
    fetchCart()
    fetchAddresses()
  }, [])

  const updateCartItem = async (item: CartItemInfo, quantity: number) =&gt; {
    try {
      if (quantity &lt;= 0) {
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

  const deleteCartItem = async (item: CartItemInfo) =&gt; {
    try {
      await cartApi.deleteCartItem(item.id)
      message.success('已删除')
      fetchCart()
    } catch (error) {
      console.error('删除购物车项失败', error)
    }
  }

  const handleCheckout = async () =&gt; {
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

  const getCartTotal = () =&gt; {
    return {
      quantity: cart.reduce((sum, item) =&gt; sum + item.quantity, 0),
      price: cart.reduce((sum, item) =&gt; sum + (item.product_price || 0) * item.quantity, 0),
    }
  }

  const cartTotal = getCartTotal()

  // 按店铺分组
  const groupedCart = cart.reduce((acc, item) =&gt; {
    if (!acc[item.shop_id]) {
      acc[item.shop_id] = []
    }
    acc[item.shop_id].push(item)
    return acc
  }, {} as Record&lt;number, CartItemInfo[]&gt;)

  if (loading) {
    return (
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  if (cart.length === 0) {
    return (
      &lt;Card&gt;
        &lt;Empty description="购物车为空" /&gt;
        &lt;div style={{ marginTop: 16, textAlign: 'center' }}&gt;
          &lt;Button type="primary" onClick={() =&gt; navigate('/user/home')}&gt;
            去逛一逛
          &lt;/Button&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    )
  }

  return (
    &lt;div&gt;
      &lt;Card&gt;
        &lt;Title level={4}&gt;购物车&lt;/Title&gt;
      &lt;/Card&gt;

      {Object.entries(groupedCart).map(([shopId, items]) =&gt; (
        &lt;Card key={shopId} style={{ marginTop: 16 }} title={items[0].shop_name}&gt;
          &lt;List
            dataSource={items}
            renderItem={(item) =&gt; (
              &lt;List.Item
                actions={[
                  &lt;Space key="actions"&gt;
                    &lt;Button
                      size="small"
                      shape="circle"
                      icon={&lt;MinusOutlined /&gt;}
                      onClick={() =&gt; updateCartItem(item, item.quantity - 1)}
                    /&gt;
                    &lt;Text&gt;{item.quantity}&lt;/Text&gt;
                    &lt;Button
                      size="small"
                      shape="circle"
                      icon={&lt;PlusOutlined /&gt;}
                      onClick={() =&gt; updateCartItem(item, item.quantity + 1)}
                    /&gt;
                    &lt;Button
                      type="text"
                      danger
                      icon={&lt;DeleteOutlined /&gt;}
                      onClick={() =&gt; deleteCartItem(item)}
                    /&gt;
                  &lt;/Space&gt;
                ]}
              &gt;
                &lt;List.Item.Meta
                  avatar={
                    item.product_image ? (
                      &lt;Image src={item.product_image} alt="" width={60} height={60} /&gt;
                    ) : (
                      &lt;div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}&gt;
                        &lt;span style={{ color: '#999' }}&gt;商品&lt;/span&gt;
                      &lt;/div&gt;
                    )
                  }
                  title={item.product_name}
                  description={
                    &lt;div&gt;
                      &lt;Text type="danger"&gt;¥{item.product_price?.toFixed(2)}&lt;/Text&gt;
                    &lt;/div&gt;
                  }
                /&gt;
              &lt;/List.Item&gt;
            )}
          /&gt;
        &lt;/Card&gt;
      ))}

      &lt;Card
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
        }}
      &gt;
        &lt;Space style={{ width: '100%', justifyContent: 'space-between' }}&gt;
          &lt;div&gt;
            &lt;Text&gt;共&lt;/Text&gt;
            &lt;Text strong style={{ marginLeft: 4, marginRight: 4 }}&gt;{cartTotal.quantity}&lt;/Text&gt;
            &lt;Text&gt;件商品，合计：&lt;/Text&gt;
            &lt;Text type="danger" strong style={{ fontSize: 18 }}&gt;¥{cartTotal.price.toFixed(2)}&lt;/Text&gt;
          &lt;/div&gt;
          &lt;Space&gt;
            &lt;Button icon={&lt;ArrowLeftOutlined /&gt;} onClick={() =&gt; navigate('/user/home')}&gt;
              继续购物
            &lt;/Button&gt;
            &lt;Button type="primary" size="large" onClick={() =&gt; setCheckoutModalVisible(true)}&gt;
              去结算
            &lt;/Button&gt;
          &lt;/Space&gt;
        &lt;/Space&gt;
      &lt;/Card&gt;

      &lt;Modal
        title="确认订单"
        open={checkoutModalVisible}
        onCancel={() =&gt; setCheckoutModalVisible(false)}
        onOk={handleCheckout}
        width={600}
      &gt;
        &lt;Form form={form} layout="vertical"&gt;
          &lt;Form.Item label="收货地址" name="address" rules={[{ required: true, message: '请选择收货地址' }]}&gt;
            &lt;Select
              placeholder="请选择收货地址"
              value={selectedAddress}
              onChange={setSelectedAddress}
              style={{ width: '100%' }}
            &gt;
              {addresses.map(address =&gt; (
                &lt;Option key={address.id} value={address.id}&gt;
                  {address.contact_name} {address.contact_phone} - {address.address}
                &lt;/Option&gt;
              ))}
            &lt;/Select&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="订单备注"&gt;
            &lt;TextArea
              value={remark}
              onChange={(e) =&gt; setRemark(e.target.value)}
              placeholder="请输入备注（选填）"
              rows={3}
            /&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;

        &lt;div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}&gt;
          &lt;Space direction="vertical" style={{ width: '100%' }}&gt;
            &lt;Text type="secondary"&gt;共{cartTotal.quantity}件商品，总计：&lt;/Text&gt;
            &lt;Text type="danger" strong style={{ fontSize: 24 }}&gt;¥{cartTotal.price.toFixed(2)}&lt;/Text&gt;
          &lt;/Space&gt;
        &lt;/div&gt;
      &lt;/Modal&gt;
    &lt;/div&gt;
  )
}

