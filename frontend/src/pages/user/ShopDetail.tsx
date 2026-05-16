
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Image, Button, Space, message, Spin, Tag } from 'antd'
import { ShoppingCartOutlined, StarOutlined, PlusOutlined, MinusOutlined, ClockCircleOutlined } from '@ant-design/icons'
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
  const [activeCategory, setActiveCategory] = useState<number | null>(null)

  const fetchShopDetail = async () => {
    if (!id) {return}
    try {
      setLoading(true)
      const res = await shopApi.getShopDetail(parseInt(id))
      setShop(res.data)
      if (res.data.categories && res.data.categories.length > 0) {
        setActiveCategory(res.data.categories[0].id)
      }
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
    if (!id) {return 0}
    const cartItem = cart.find((item) => item.shop_id === parseInt(id) && item.product_id === productId)
    return cartItem?.quantity || 0
  }

  const addToCart = async (product: ProductInfo) => {
    if (!id) {return}
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
    if (!id) {return}
    const cartItem = cart.find((item) => item.shop_id === parseInt(id) && item.product_id === product.id)
    if (!cartItem) {return}

    try {
      if (quantity <= 0) {
        await cartApi.deleteCartItem(cartItem.id)
      } else {
        await cartApi.updateCartItem(cartItem.id, { quantity })
      }
      fetchCart()
    } catch (error) {
      console.error('更新购物车失败', error)
    }
  }

  const getCartTotalForShop = () => {
    if (!id) {return { quantity: 0, price: 0 }}
    const shopCart = cart.filter((item) => item.shop_id === parseInt(id))
    return {
      quantity: shopCart.reduce((sum, item) => sum + item.quantity, 0),
      price: shopCart.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0),
    }
  }

  const cartTotal = getCartTotalForShop()
  const minOrderAmount = shop?.min_order_amount || 0
  const diffToMinOrder = minOrderAmount - cartTotal.price

  const renderProductItem = (product: ProductInfo) => {
    const count = getProductCountInCart(product.id)
    return (
      <div
        key={product.id}
        style={{
          display: 'flex', gap: isMobile ? 8 : 12,
          padding: isMobile ? '10px 0' : '12px 0',
          borderBottom: '1px solid #f5f5f5',
        }}
      >
        {product.image ? (
          <Image
            src={product.image} alt=""
            width={isMobile ? 64 : 80} height={isMobile ? 64 : 80}
            style={{ borderRadius: 8, flexShrink: 0, objectFit: 'cover' }}
            preview={false}
          />
        ) : (
          <div style={{
            width: isMobile ? 64 : 80, height: isMobile ? 64 : 80, background: '#f0f0f0',
            borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, fontSize: 12, color: '#999',
          }}>
            商品
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: isMobile ? 13 : 14, marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {product.name}
          </div>
          {product.description && (
            <div style={{ fontSize: 11, color: '#999', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {product.description}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <Text type="danger" strong style={{ fontSize: isMobile ? 15 : 17 }}>¥{product.price.toFixed(2)}</Text>
              {product.original_price && product.original_price > product.price && (
                <Text delete style={{ marginLeft: 6, fontSize: 11, color: '#999' }}>¥{product.original_price.toFixed(2)}</Text>
              )}
            </div>
            <div>
              {count > 0 ? (
                <Space size={4}>
                  <Button
                    size="small" shape="circle" icon={<MinusOutlined />}
                    onClick={(e) => { e.stopPropagation(); updateCartItem(product, count - 1) }}
                  />
                  <Text strong style={{ minWidth: 20, textAlign: 'center' }}>{count}</Text>
                  <Button
                    size="small" shape="circle" type="primary" icon={<PlusOutlined />}
                    onClick={(e) => { e.stopPropagation(); updateCartItem(product, count + 1) }}
                  />
                </Space>
              ) : (
                <Button
                  type="primary" size="small"
                  icon={<PlusOutlined />}
                  onClick={(e) => { e.stopPropagation(); addToCart(product) }}
                  style={{ borderRadius: 16 }}
                >
                  加入
                </Button>
              )}
            </div>
          </div>
          {product.sales > 0 && (
            <Text type="secondary" style={{ fontSize: 10 }}>月售{product.sales}</Text>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>
  }

  if (!shop) {
    return <div>店铺不存在</div>
  }

  const categories = shop.categories || []
  const activeCategoryData = categories.find((c) => c.id === activeCategory)
  const activeProducts = activeCategoryData?.products?.filter((p) => p.status === 1) || []

  return (
    <div>
      <div style={{
        background: 'linear-gradient(135deg, #ff9a44, #fc6076)',
        padding: isMobile ? '16px' : '24px',
        borderRadius: isMobile ? 0 : 12,
        marginBottom: isMobile ? 0 : 16,
        color: '#fff',
      }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {shop.logo ? (
            <Image src={shop.logo} alt="" width={isMobile ? 56 : 72} height={isMobile ? 56 : 72} style={{ borderRadius: 10, flexShrink: 0 }} preview={false} />
          ) : (
            <div style={{
              width: isMobile ? 56 : 72, height: isMobile ? 56 : 72, background: 'rgba(255,255,255,0.3)',
              borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, fontSize: 28,
            }}>
              🏪
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: isMobile ? 17 : 20, fontWeight: 700, marginBottom: 4 }}>{shop.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
              <span><StarOutlined style={{ color: '#faad14' }} /> {shop.rating}</span>
              <span>月售{shop.monthly_sales}+</span>
              <span><ClockCircleOutlined /> 约{shop.delivery_time}</span>
            </div>
            <div style={{ fontSize: 12, marginTop: 4, opacity: 0.9 }}>
              ¥{shop.min_order_amount}起送 | 配送费¥{shop.delivery_fee}
            </div>
          </div>
        </div>
        {shop.notice && (
          <div style={{ marginTop: 10, fontSize: 12, opacity: 0.9, background: 'rgba(255,255,255,0.15)', padding: '6px 10px', borderRadius: 6 }}>
            📢 {shop.notice}
          </div>
        )}
        <div style={{ marginTop: 8, display: 'flex', gap: 4 }}>
          {(() => {
            try {
              const discountList: string[] = shop.discounts ? JSON.parse(shop.discounts) : []
              return discountList.map((d, i) => (
                <Tag key={i} color="volcano" style={{ margin: 0, fontSize: 11 }}>{d}</Tag>
              ))
            } catch {
              return null
            }
          })()}
        </div>
      </div>

      {isMobile ? (
        <div style={{ display: 'flex', background: '#fff', minHeight: 'calc(100vh - 300px)' }}>
          <div style={{
            width: 80, flexShrink: 0, background: '#f5f5f5',
            overflowY: 'auto', borderRight: '1px solid #f0f0f0',
          }}>
            {categories.map((cat) => (
              <div
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                style={{
                  padding: '12px 6px', fontSize: 12, textAlign: 'center',
                  cursor: 'pointer', transition: 'all 0.2s',
                  background: activeCategory === cat.id ? '#fff' : 'transparent',
                  color: activeCategory === cat.id ? '#1890ff' : '#666',
                  fontWeight: activeCategory === cat.id ? 600 : 400,
                  borderLeft: activeCategory === cat.id ? '3px solid #1890ff' : '3px solid transparent',
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}
              >
                {cat.name}
              </div>
            ))}
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 10px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, padding: '10px 0 4px', color: '#333' }}>
              {activeCategoryData?.name}
            </div>
            {activeProducts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 30, color: '#999' }}>暂无商品</div>
            ) : (
              activeProducts.map(renderProductItem)
            )}
          </div>
        </div>
      ) : (
        <Card>
          <div style={{ display: 'flex', gap: 0 }}>
            <div style={{
              width: 120, flexShrink: 0, borderRight: '1px solid #f0f0f0',
              marginRight: 16,
            }}>
              {categories.map((cat) => (
                <div
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  style={{
                    padding: '10px 12px', fontSize: 13, cursor: 'pointer',
                    background: activeCategory === cat.id ? '#e6f7ff' : 'transparent',
                    color: activeCategory === cat.id ? '#1890ff' : '#666',
                    fontWeight: activeCategory === cat.id ? 600 : 400,
                    borderRight: activeCategory === cat.id ? '3px solid #1890ff' : '3px solid transparent',
                    borderRadius: activeCategory === cat.id ? '4px 0 0 4px' : 0,
                    marginBottom: 2,
                  }}
                >
                  {cat.name}
                </div>
              ))}
            </div>
            <div style={{ flex: 1 }}>
              <Title level={5} style={{ margin: '0 0 12px 0' }}>{activeCategoryData?.name}</Title>
              {activeProducts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 30, color: '#999' }}>暂无商品</div>
              ) : (
                activeProducts.map(renderProductItem)
              )}
            </div>
          </div>
        </Card>
      )}

      {cartTotal.quantity > 0 && (
        <div
          style={{
            position: 'fixed',
            bottom: isMobile ? 56 : 0,
            left: 0,
            right: 0,
            background: '#333',
            padding: '8px 16px',
            zIndex: 99,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ position: 'relative' }}>
              <ShoppingCartOutlined style={{ fontSize: 28, color: '#1890ff' }} />
              <span style={{
                position: 'absolute', top: -8, right: -8,
                background: '#ff4d4f', color: '#fff', fontSize: 10,
                borderRadius: 10, padding: '0 5px', lineHeight: '16px',
                fontWeight: 700,
              }}>
                {cartTotal.quantity}
              </span>
            </div>
            <div>
              <Text style={{ color: '#fff', fontWeight: 700, fontSize: 18 }}>¥{cartTotal.price.toFixed(2)}</Text>
              {diffToMinOrder > 0 && (
                <div style={{ fontSize: 10, color: '#faad14' }}>再选¥{diffToMinOrder.toFixed(0)}满足¥{minOrderAmount}起送</div>
              )}
            </div>
          </div>
          <Button
            type="primary"
            size="large"
            style={{ borderRadius: 20, minWidth: 100, fontWeight: 600 }}
            onClick={() => navigate('/user/cart')}
          >
            去结算
          </Button>
        </div>
      )}
    </div>
  )
}
