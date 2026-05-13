
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Tabs, List, Image, Button, Space, message, Spin } from 'antd'
import { ShoppingCartOutlined, StarOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons'
import { shopApi, ShopDetail as ShopDetailType, ProductInfo } from '../../services/shop'
import { cartApi, CartItemInfo } from '../../services/order'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

export default function ShopDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [shop, setShop] = useState<ShopDetailType | null>(null)
  const [cart, setCart] = useState<CartItemInfo[]>([])

  const fetchShopDetail = async () => {
    if (!id) return
    try {
      setLoading(true)
      const res = await shopApi.getShopDetail(parseInt(id))
      setShop(res.data)
    } catch (error) {
      console.error('获取商家详情失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchCart = async () => {
    try {
      const res = await cartApi.getCart()
      setCart(res.data)
    } catch (error) {
      console.error('获取购物车失败', error)
    }
  }

  useEffect(() => {
    fetchShopDetail()
    fetchCart()
  }, [id])

  const getProductCountInCart = (productId: number) => {
    if (!id) return 0
    const cartItem = cart.find(item => item.shop_id === parseInt(id) && item.product_id === productId)
    return cartItem?.quantity || 0
  }

  const addToCart = async (product: ProductInfo) => {
    if (!id) return
    try {
      await cartApi.addToCart({
        shop_id: parseInt(id),
        product_id: product.id,
        quantity: 1,
      })
      message.success('已加入购物车')
      fetchCart()
    } catch (error) {
      console.error('添加购物车失败', error)
    }
  }

  const updateCartItem = async (product: ProductInfo, quantity: number) => {
    if (!id) return
    const cartItem = cart.find(item => item.shop_id === parseInt(id) && item.product_id === product.id)
    if (!cartItem) return

    try {
      if (quantity <= 0) {
        await cartApi.deleteCartItem(cartItem.id)
      } else {
        await cartApi.updateCartItem(cartItem.id, { quantity })
      }
      message.success('购物车已更新')
      fetchCart()
    } catch (error) {
      console.error('更新购物车失败', error)
    }
  }

  const getCartTotalForShop = () => {
    if (!id) return { quantity: 0, price: 0 }
    const shopCart = cart.filter(item => item.shop_id === parseInt(id))
    return {
      quantity: shopCart.reduce((sum, item) => sum + item.quantity, 0),
      price: shopCart.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0),
    }
  }

  const cartTotal = getCartTotalForShop()

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!shop) {
    return <div>店铺不存在</div>
  }

  const tabItems = (shop.categories || []).map(category => ({
    key: category.id.toString(),
    label: category.name,
    children: (
      <List
        dataSource={category.products?.filter(p => p.status === 1)}
        renderItem={product => {
          const count = getProductCountInCart(product.id)
          return (
            <List.Item style={{ padding: isMobile ? '8px 0' : undefined }}>
              <Space style={{ width: '100%', flexWrap: isMobile ? 'wrap' : 'nowrap' }}>
                {product.image ? (
                  <Image src={product.image} alt="" width={isMobile ? 60 : 80} height={isMobile ? 60 : 80} style={{ borderRadius: 6 }} />
                ) : (
                  <div style={{
                    width: isMobile ? 60 : 80, height: isMobile ? 60 : 80, background: '#f0f0f0',
                    borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <span style={{ color: '#999' }}>商品</span>
                  </div>
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Title level={5} style={{ margin: 0 }}>{product.name}</Title>
                  {product.description && <Text type="secondary" style={{ fontSize: 12 }}>{product.description}</Text>}
                  <div style={{ marginTop: 4 }}>
                    <Text type="danger" strong style={{ fontSize: isMobile ? 16 : 18 }}>¥{product.price.toFixed(2)}</Text>
                    {product.original_price && product.original_price > product.price && (
                      <Text delete style={{ marginLeft: 8, fontSize: 12 }}>¥{product.original_price.toFixed(2)}</Text>
                    )}
                  </div>
                </div>
                <Space>
                  {count > 0 ? (
                    <>
                      <Button
                        size="small"
                        shape="circle"
                        icon={<MinusOutlined />}
                        onClick={() => updateCartItem(product, count - 1)}
                      />
                      <Text>{count}</Text>
                      <Button
                        size="small"
                        shape="circle"
                        icon={<PlusOutlined />}
                        onClick={() => updateCartItem(product, count + 1)}
                      />
                    </>
                  ) : (
                    <Button
                      type="primary"
                      size="small"
                      icon={<PlusOutlined />}
                      onClick={() => addToCart(product)}
                    >
                      加入购物车
                    </Button>
                  )}
                </Space>
              </Space>
            </List.Item>
          )
        }}
      />
    ),
  }))

  return (
    <div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            {shop.logo ? (
              <Image src={shop.logo} alt="" width={isMobile ? 60 : 80} height={isMobile ? 60 : 80} style={{ borderRadius: 8 }} />
            ) : (
              <div style={{
                width: isMobile ? 60 : 80, height: isMobile ? 60 : 80, background: '#f0f0f0',
                borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <span style={{ color: '#999' }}>店铺</span>
              </div>
            )}
            <div>
              <Title level={isMobile ? 5 : 4} style={{ margin: 0 }}>{shop.name}</Title>
              <Text><StarOutlined style={{ color: '#faad14' }} /> {shop.rating}</Text>
            </div>
          </Space>
          {shop.notice && (
            <div>
              <Text type="secondary">店铺公告：</Text>
              <Text>{shop.notice}</Text>
            </div>
          )}
        </Space>
      </Card>

      <Card style={{ marginTop: isMobile ? 8 : 16 }}>
        <Tabs defaultActiveKey={shop.categories?.[0]?.id?.toString() || '0'} items={tabItems} />
      </Card>

      {cartTotal.quantity > 0 && (
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
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <ShoppingCartOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <div>
                  <Text type="danger" strong style={{ fontSize: 18 }}>¥{cartTotal.price.toFixed(2)}</Text>
                  <Text type="secondary" style={{ marginLeft: 8 }}>共{cartTotal.quantity}件</Text>
                </div>
              </div>
            </Space>
            <Button
              type="primary"
              size="large"
              onClick={() => navigate(`/user/cart`)}
            >
              去购物车
            </Button>
          </Space>
        </Card>
      )}
    </div>
  )
}
