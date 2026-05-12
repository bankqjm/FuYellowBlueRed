
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Tabs, List, Image, Button, Space, message, Spin, Divider } from 'antd'
import { ShoppingCartOutlined, StarOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons'
import { shopApi, ShopDetail, ProductInfo, CategoryInfo } from '../../services/shop'
import { cartApi, CartItemInfo } from '../../services/order'

const { Title, Text } = Typography
const { TabPane } = Tabs

export default function ShopDetail() {
  const { id } = useParams&lt;{ id: string }&gt;()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [shop, setShop] = useState&lt;ShopDetail | null&gt;(null)
  const [cart, setCart] = useState&lt;CartItemInfo[]&gt;([])

  const fetchShopDetail = async () =&gt; {
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

  const fetchCart = async () =&gt; {
    try {
      const res = await cartApi.getCart()
      setCart(res.data)
    } catch (error) {
      console.error('获取购物车失败', error)
    }
  }

  useEffect(() =&gt; {
    fetchShopDetail()
    fetchCart()
  }, [id])

  const getProductCountInCart = (productId: number) =&gt; {
    if (!id) return 0
    const cartItem = cart.find(item =&gt; item.shop_id === parseInt(id) &amp;&amp; item.product_id === productId)
    return cartItem?.quantity || 0
  }

  const addToCart = async (product: ProductInfo) =&gt; {
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

  const updateCartItem = async (product: ProductInfo, quantity: number) =&gt; {
    if (!id) return
    const cartItem = cart.find(item =&gt; item.shop_id === parseInt(id) &amp;&amp; item.product_id === product.id)
    if (!cartItem) return

    try {
      if (quantity &lt;= 0) {
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

  const getCartTotalForShop = () =&gt; {
    if (!id) return { quantity: 0, price: 0 }
    const shopCart = cart.filter(item =&gt; item.shop_id === parseInt(id))
    return {
      quantity: shopCart.reduce((sum, item) =&gt; sum + item.quantity, 0),
      price: shopCart.reduce((sum, item) =&gt; sum + (item.product_price || 0) * item.quantity, 0),
    }
  }

  const cartTotal = getCartTotalForShop()

  if (loading) {
    return (
      &lt;div style={{ textAlign: 'center', padding: 50 }}&gt;
        &lt;Spin size="large" /&gt;
      &lt;/div&gt;
    )
  }

  if (!shop) {
    return &lt;div&gt;店铺不存在&lt;/div&gt;
  }

  return (
    &lt;div&gt;
      &lt;Card&gt;
        &lt;Space direction="vertical" style={{ width: '100%' }}&gt;
          &lt;Space&gt;
            {shop.logo ? (
              &lt;Image src={shop.logo} alt="" width={80} height={80} /&gt;
            ) : (
              &lt;div style={{ width: 80, height: 80, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}&gt;
                &lt;span style={{ color: '#999' }}&gt;店铺&lt;/span&gt;
              &lt;/div&gt;
            )}
            &lt;div&gt;
              &lt;Title level={4} style={{ margin: 0 }}&gt;{shop.name}&lt;/Title&gt;
              &lt;Text&gt;&lt;StarOutlined style={{ color: '#faad14' }} /&gt; {shop.rating}&lt;/Text&gt;
            &lt;/div&gt;
          &lt;/Space&gt;
          {shop.notice &amp;&amp; (
            &lt;div&gt;
              &lt;Text type="secondary"&gt;店铺公告：&lt;/Text&gt;
              &lt;Text&gt;{shop.notice}&lt;/Text&gt;
            &lt;/div&gt;
          )}
        &lt;/Space&gt;
      &lt;/Card&gt;

      &lt;Card style={{ marginTop: 16 }}&gt;
        &lt;Tabs defaultActiveKey={shop.categories?.[0]?.id?.toString() || '0'}&gt;
          {shop.categories?.map(category =&gt; (
            &lt;TabPane tab={category.name} key={category.id.toString()}&gt;
              &lt;List
                dataSource={category.products?.filter(p =&gt; p.status === 1)}
                renderItem={product =&gt; {
                  const count = getProductCountInCart(product.id)
                  return (
                    &lt;List.Item&gt;
                      &lt;Space style={{ width: '100%' }}&gt;
                        {product.image ? (
                          &lt;Image src={product.image} alt="" width={80} height={80} /&gt;
                        ) : (
                          &lt;div style={{ width: 80, height: 80, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}&gt;
                            &lt;span style={{ color: '#999' }}&gt;商品&lt;/span&gt;
                          &lt;/div&gt;
                        )}
                        &lt;div style={{ flex: 1 }}&gt;
                          &lt;Title level={5} style={{ margin: 0 }}&gt;{product.name}&lt;/Title&gt;
                          {product.description &amp;&amp; &lt;Text type="secondary"&gt;{product.description}&lt;/Text&gt;}
                          &lt;div style={{ marginTop: 8 }}&gt;
                            &lt;Text type="danger" strong style={{ fontSize: 18 }}&gt;¥{product.price.toFixed(2)}&lt;/Text&gt;
                            {product.original_price &amp;&amp; product.original_price &gt; product.price &amp;&amp; (
                              &lt;Text delete style={{ marginLeft: 8 }}&gt;¥{product.original_price.toFixed(2)}&lt;/Text&gt;
                            )}
                          &lt;/div&gt;
                        &lt;/div&gt;
                        &lt;Space&gt;
                          {count &gt; 0 ? (
                            &lt;&gt;
                              &lt;Button
                                size="small"
                                shape="circle"
                                icon={&lt;MinusOutlined /&gt;}
                                onClick={() =&gt; updateCartItem(product, count - 1)}
                              /&gt;
                              &lt;Text&gt;{count}&lt;/Text&gt;
                              &lt;Button
                                size="small"
                                shape="circle"
                                icon={&lt;PlusOutlined /&gt;}
                                onClick={() =&gt; updateCartItem(product, count + 1)}
                              /&gt;
                            &lt;/&gt;
                          ) : (
                            &lt;Button
                              type="primary"
                              size="small"
                              icon={&lt;PlusOutlined /&gt;}
                              onClick={() =&gt; addToCart(product)}
                            &gt;
                              加入购物车
                            &lt;/Button&gt;
                          )}
                        &lt;/Space&gt;
                      &lt;/Space&gt;
                    &lt;/List.Item&gt;
                  )
                }}
              /&gt;
            &lt;/TabPane&gt;
          ))}
        &lt;/Tabs&gt;
      &lt;/Card&gt;

      {cartTotal.quantity &gt; 0 &amp;&amp; (
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
            &lt;Space&gt;
              &lt;ShoppingCartOutlined style={{ fontSize: 24, color: '#1890ff' }} /&gt;
              &lt;div&gt;
                &lt;div&gt;
                  &lt;Text type="danger" strong style={{ fontSize: 18 }}&gt;¥{cartTotal.price.toFixed(2)}&lt;/Text&gt;
                  &lt;Text type="secondary" style={{ marginLeft: 8 }}&gt;共{cartTotal.quantity}件&lt;/Text&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/Space&gt;
            &lt;Button
              type="primary"
              size="large"
              onClick={() =&gt; navigate(`/user/cart`)}
            &gt;
              去购物车
            &lt;/Button&gt;
          &lt;/Space&gt;
        &lt;/Card&gt;
      )}
    &lt;/div&gt;
  )
}

