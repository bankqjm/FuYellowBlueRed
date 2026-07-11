
import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Image, Button, Space, message, Spin, Tag, Tabs, List, Avatar, Empty, Rate, Drawer, Input, Segmented } from 'antd'
import { ShoppingCartOutlined, StarOutlined, PlusOutlined, MinusOutlined, ClockCircleOutlined, HeartOutlined, HeartFilled, SearchOutlined } from '@ant-design/icons'
import { shopApi, ShopDetail as ShopDetailType, ProductInfo } from '../../services/shop'
import { cartApi, CartItemInfo } from '../../services/order'
import { favoritesApi } from '../../services/favorites'
import { reviewApi, ReviewInfo } from '../../services/review'
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
  const [cartBadgeBounce, setCartBadgeBounce] = useState(false)
  const [flyingDots, setFlyingDots] = useState<{ id: number; x: number; y: number; flyX: number; flyY: number }[]>([])
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('menu')
  const [reviews, setReviews] = useState<ReviewInfo[]>([])
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [reviewTotal, setReviewTotal] = useState(0)
  const [reviewPage, setReviewPage] = useState(1)
  const [productDrawerVisible, setProductDrawerVisible] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<ProductInfo | null>(null)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [sortBy, setSortBy] = useState<string>('default')
  const dotIdRef = useRef(0)
  const cartIconRef = useRef<HTMLSpanElement>(null)

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

  const checkFavorite = async () => {
    if (!id) {return}
    try {
      const res = await favoritesApi.checkFavorite(parseInt(id))
      setIsFavorited(res.data?.is_favorited || false)
    } catch {
      // 未登录或接口异常，忽略
    }
  }

  const toggleFavorite = async () => {
    if (!id) {return}
    try {
      setFavoriteLoading(true)
      if (isFavorited) {
        await favoritesApi.removeFavorite(parseInt(id))
        setIsFavorited(false)
        message.success('已取消收藏')
      } else {
        await favoritesApi.addFavorite(parseInt(id))
        setIsFavorited(true)
        message.success('已收藏')
      }
    } catch {
      // error handled by interceptor
    } finally {
      setFavoriteLoading(false)
    }
  }

  const fetchReviews = async (page = 1) => {
    if (!id) {return}
    try {
      setReviewsLoading(true)
      const res = await reviewApi.getShopReviews(parseInt(id), { page, page_size: 10 })
      setReviews(res.data?.items || [])
      setReviewTotal(res.data?.total || 0)
      setReviewPage(page)
    } catch {
      // error handled by interceptor
    } finally {
      setReviewsLoading(false)
    }
  }

  useEffect(() => {
    fetchShopDetail()
    fetchCart()
    checkFavorite()
  }, [id])

  useEffect(() => {
    if (activeTab === 'reviews' && id) {
      fetchReviews(1)
    }
  }, [activeTab, id])

  const cartProductMap = useMemo(() => {
    if (!id) {return new Map<number, number>()}
    const map = new Map<number, number>()
    cart.filter((item) => item.shop_id === parseInt(id!)).forEach((item) => {
      map.set(item.product_id, item.quantity)
    })
    return map
  }, [cart, id])

  const cartTotal = useMemo(() => {
    if (!id) {return { quantity: 0, price: 0 }}
    const shopCart = cart.filter((item) => item.shop_id === parseInt(id!))
    return {
      quantity: shopCart.reduce((sum, item) => sum + item.quantity, 0),
      price: shopCart.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0),
    }
  }, [cart, id])

  const discountList = useMemo(() => {
    try {
      return shop?.discounts ? JSON.parse(shop.discounts) : []
    } catch {
      return []
    }
  }, [shop?.discounts])

  const minOrderAmount = shop?.min_order_amount || 0
  const diffToMinOrder = minOrderAmount - cartTotal.price

  const categories = shop?.categories || []
  const activeCategoryData = categories.find((c) => c.id === activeCategory)
  const activeProducts = activeCategoryData?.products?.filter((p) => p.status === 1) || []

  const filteredAndSortedProducts = useMemo(() => {
    let products = activeProducts
    if (searchKeyword) {
      products = products.filter(p => p.name.includes(searchKeyword) || (p.description && p.description.includes(searchKeyword)))
    }
    if (sortBy === 'price') {
      products = [...products].sort((a, b) => a.price - b.price)
    } else if (sortBy === 'price_desc') {
      products = [...products].sort((a, b) => b.price - a.price)
    } else if (sortBy === 'sales') {
      products = [...products].sort((a, b) => b.sales - a.sales)
    }
    return products
  }, [activeProducts, searchKeyword, sortBy])

  const triggerCartAnimation = useCallback((btnEl: HTMLElement | null) => {
    if (!btnEl || !cartIconRef.current) {return}

    const btnRect = btnEl.getBoundingClientRect()
    const cartRect = cartIconRef.current.getBoundingClientRect()

    const dotId = ++dotIdRef.current
    const startX = btnRect.left + btnRect.width / 2
    const startY = btnRect.top + btnRect.height / 2
    const flyX = cartRect.left + cartRect.width / 2 - startX
    const flyY = cartRect.top + cartRect.height / 2 - startY

    setFlyingDots((prev) => [...prev, { id: dotId, x: startX, y: startY, flyX, flyY }])

    setTimeout(() => {
      setFlyingDots((prev) => prev.filter((d) => d.id !== dotId))
    }, 600)

    setCartBadgeBounce(true)
    setTimeout(() => setCartBadgeBounce(false), 500)
  }, [])

  const addToCart = async (product: ProductInfo, btnEl: HTMLElement | null) => {
    if (!id) {return}
    try {
      await cartApi.addToCart({
        shop_id: parseInt(id),
        product_id: product.id,
        quantity: 1,
      })
      message.success('已加入购物车')
      triggerCartAnimation(btnEl)
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

  const showProductDetail = (product: ProductInfo) => {
    setSelectedProduct(product)
    setProductDrawerVisible(true)
  }

  const renderProductItem = (product: ProductInfo) => {
    const count = cartProductMap.get(product.id) || 0
    const isSoldOut = product.stock === 0
    return (
      <div
        key={product.id}
        onClick={() => !isSoldOut && showProductDetail(product)}
        style={{
          display: 'flex', gap: isMobile ? 8 : 12,
          padding: isMobile ? '10px 0' : '12px 0',
          borderBottom: '1px solid #f5f5f5',
          cursor: isSoldOut ? 'not-allowed' : 'pointer',
          position: 'relative',
          opacity: isSoldOut ? 0.55 : 1,
        }}
      >
        {product.image ? (
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <Image
              src={product.image} alt=""
              width={isMobile ? 64 : 80} height={isMobile ? 64 : 80}
              style={{ borderRadius: 8, objectFit: 'cover' }}
              preview={false}
            />
            {isSoldOut && (
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.45)', borderRadius: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontSize: 14, fontWeight: 600,
              }}>
                售罄
              </div>
            )}
          </div>
        ) : (
          <div style={{
            width: isMobile ? 64 : 80, height: isMobile ? 64 : 80, background: '#f0f0f0',
            borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, fontSize: 12, color: '#999', position: 'relative',
          }}>
            商品
            {isSoldOut && (
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.45)', borderRadius: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontSize: 14, fontWeight: 600,
              }}>
                售罄
              </div>
            )}
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
            <span style={{ fontWeight: 600, fontSize: isMobile ? 13 : 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {product.name}
            </span>
            {product.tags && JSON.parse(product.tags).map((tag: string, i: number) => (
              <Tag key={i} color="orange" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}>{tag}</Tag>
            ))}
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
            {!isSoldOut && (
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
                    onClick={(e) => {
                      e.stopPropagation()
                      const btn = (e.target as HTMLElement).closest('button')
                      addToCart(product, btn)
                    }}
                    style={{ borderRadius: 16 }}
                    className="add-btn-pulse"
                  >
                    加入
                  </Button>
                )}
              </div>
            )}
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

  const renderMenuContent = () => (
    isMobile ? (
      <div style={{ display: 'flex', background: '#fff', minHeight: 'calc(100vh - 350px)' }}>
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
          <div style={{ marginBottom: 8 }}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索菜品"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              allowClear
              size="small"
              style={{ marginBottom: 6 }}
            />
            <Segmented
              size="small"
              value={sortBy}
              onChange={(val) => setSortBy(val as string)}
              options={[
                { label: '默认', value: 'default' },
                { label: '价格↑', value: 'price' },
                { label: '价格↓', value: 'price_desc' },
                { label: '销量', value: 'sales' },
              ]}
            />
          </div>
          {filteredAndSortedProducts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#999' }}>暂无商品</div>
          ) : (
            filteredAndSortedProducts.map(renderProductItem)
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
            <div style={{ marginBottom: 12 }}>
              <Input
                prefix={<SearchOutlined />}
                placeholder="搜索菜品"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                allowClear
                size="small"
                style={{ marginBottom: 6 }}
              />
              <Segmented
                size="small"
                value={sortBy}
                onChange={(val) => setSortBy(val as string)}
                options={[
                  { label: '默认', value: 'default' },
                  { label: '价格↑', value: 'price' },
                  { label: '价格↓', value: 'price_desc' },
                  { label: '销量', value: 'sales' },
                ]}
              />
            </div>
            {filteredAndSortedProducts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 30, color: '#999' }}>暂无商品</div>
            ) : (
              filteredAndSortedProducts.map(renderProductItem)
            )}
          </div>
        </div>
      </Card>
    )
  )

  const renderReviewsContent = () => (
    <Card>
      {reviewsLoading ? (
        <div style={{ textAlign: 'center', padding: 30 }}><Spin /></div>
      ) : reviews.length === 0 ? (
        <Empty description="暂无评价" />
      ) : (
        <List
          dataSource={reviews}
          pagination={reviewTotal > 10 ? {
            current: reviewPage,
            total: reviewTotal,
            pageSize: 10,
            onChange: (page) => fetchReviews(page),
          } : undefined}
          renderItem={(review: ReviewInfo) => (
            <List.Item>
              <div style={{ width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Avatar size="small" style={{ backgroundColor: '#1890ff' }}>
                    {(review.user_nickname || '用户')[0]}
                  </Avatar>
                  <Text strong style={{ fontSize: 13 }}>{review.user_nickname || '匿名用户'}</Text>
                  <Rate disabled value={review.shop_rating} style={{ fontSize: 12 }} />
                </div>
                {review.content && (
                  <div style={{ fontSize: 13, color: '#333', marginBottom: 4 }}>{review.content}</div>
                )}
                {review.images && review.images.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {review.images.map((img, i) => (
                      <Image key={i} src={img} width={60} height={60} style={{ borderRadius: 4, objectFit: 'cover' }} />
                    ))}
                  </div>
                )}
                {review.rider_rating && (
                  <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                    骑手评分：<Rate disabled value={review.rider_rating} style={{ fontSize: 10 }} />
                  </div>
                )}
                {review.created_at && (
                  <div style={{ fontSize: 11, color: '#bfbfbf', marginTop: 4 }}>{review.created_at}</div>
                )}
              </div>
            </List.Item>
          )}
        />
      )}
    </Card>
  )

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
          <Button
            type="text"
            loading={favoriteLoading}
            onClick={toggleFavorite}
            style={{ color: '#fff', fontSize: 24 }}
          >
            {isFavorited ? <HeartFilled style={{ color: '#ff4d4f' }} /> : <HeartOutlined />}
          </Button>
        </div>
        {shop.notice && (
          <div style={{ marginTop: 10, fontSize: 12, opacity: 0.9, background: 'rgba(255,255,255,0.15)', padding: '6px 10px', borderRadius: 6 }}>
            📢 {shop.notice}
          </div>
        )}
        <div style={{ marginTop: 8, display: 'flex', gap: 4 }}>
          {discountList.map((d: string, i: number) => (
            <Tag key={i} color="volcano" style={{ margin: 0, fontSize: 11 }}>{d}</Tag>
          ))}
        </div>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        centered
        items={[
          { key: 'menu', label: '菜单' },
          { key: 'reviews', label: `评价(${reviewTotal || 0})` },
        ]}
        style={{ marginBottom: 0 }}
      />

      {activeTab === 'menu' ? renderMenuContent() : renderReviewsContent()}

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
              <ShoppingCartOutlined ref={cartIconRef} style={{ fontSize: 28, color: '#1890ff' }} />
              <span
                className={cartBadgeBounce ? 'cart-badge-bounce' : ''}
                style={{
                  position: 'absolute', top: -8, right: -8,
                  background: '#ff4d4f', color: '#fff', fontSize: 10,
                  borderRadius: 10, padding: '0 5px', lineHeight: '16px',
                  fontWeight: 700,
                }}
              >
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

      {flyingDots.map((dot) => (
        <div
          key={dot.id}
          className="fly-dot"
          style={{
            left: dot.x - 7,
            top: dot.y - 7,
            '--fly-x': `${dot.flyX}px`,
            '--fly-y': `${dot.flyY}px`,
          } as React.CSSProperties}
        />
      ))}

      <Drawer
        title={selectedProduct?.name}
        placement="right"
        onClose={() => setProductDrawerVisible(false)}
        open={productDrawerVisible}
        width={isMobile ? '85%' : 400}
      >
        {selectedProduct && (
          <div>
            {selectedProduct.image && (
              <Image src={selectedProduct.image} alt="" style={{ width: '100%', borderRadius: 8, marginBottom: 16 }} />
            )}
            <div style={{ marginBottom: 8 }}>
              <Text type="danger" strong style={{ fontSize: 24 }}>¥{selectedProduct.price.toFixed(2)}</Text>
              {selectedProduct.original_price && selectedProduct.original_price > selectedProduct.price && (
                <Text delete style={{ marginLeft: 8, fontSize: 14, color: '#999' }}>¥{selectedProduct.original_price.toFixed(2)}</Text>
              )}
            </div>
            {selectedProduct.description && (
              <div style={{ color: '#666', marginBottom: 12, lineHeight: 1.6 }}>{selectedProduct.description}</div>
            )}
            <div style={{ display: 'flex', gap: 16, marginBottom: 16, color: '#999', fontSize: 13 }}>
              <span>月售{selectedProduct.sales}</span>
              <span>库存{selectedProduct.stock}</span>
            </div>
            {selectedProduct.tags && JSON.parse(selectedProduct.tags).map((tag: string, i: number) => (
              <Tag key={i} color="orange" style={{ marginBottom: 4 }}>{tag}</Tag>
            ))}
            <div style={{ marginTop: 24 }}>
              {selectedProduct.stock > 0 ? (
                <Button type="primary" size="large" block icon={<PlusOutlined />}
                  onClick={() => {
                    addToCart(selectedProduct, null)
                    setProductDrawerVisible(false)
                  }}
                >
                  加入购物车 ¥{selectedProduct.price.toFixed(2)}
                </Button>
              ) : (
                <Button size="large" block disabled>已售罄</Button>
              )}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}
