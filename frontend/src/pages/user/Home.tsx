import { Input, List, Typography, Space, Empty, Spin, Tag, Image, Carousel, Select } from 'antd'
import {
  SearchOutlined,
  EnvironmentOutlined,
  StarOutlined,
  ClockCircleOutlined,
  ShoppingOutlined,
  FireOutlined,
  CarOutlined,
  CoffeeOutlined,
  GiftOutlined,
  MedicineBoxOutlined,
  AppleOutlined,
  HeartOutlined,
  CrownOutlined,
  ThunderboltOutlined,
  DeleteOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { shopApi, ShopInfo } from '../../services/shop'
import { addressApi, AddressInfo } from '../../services/address'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

const categoryItems = [
  { icon: <FireOutlined />, label: '美食', color: '#ff4d4f' },
  { icon: <CoffeeOutlined />, label: '甜品饮品', color: '#fa8c16' },
  { icon: <ShoppingOutlined />, label: '超市便利', color: '#1890ff' },
  { icon: <AppleOutlined />, label: '果蔬生鲜', color: '#52c41a' },
  { icon: <MedicineBoxOutlined />, label: '医药健康', color: '#722ed1' },
  { icon: <CarOutlined />, label: '跑腿代购', color: '#13c2c2' },
  { icon: <GiftOutlined />, label: '优惠活动', color: '#eb2f96' },
  { icon: <HeartOutlined />, label: '轻食沙拉', color: '#f5222d' },
  { icon: <CrownOutlined />, label: '品质优选', color: '#faad14' },
  { icon: <ThunderboltOutlined />, label: '准时达', color: '#2f54eb' },
]

const sortOptions = [
  { label: '综合排序', value: 'default' },
  { label: '距离最近', value: 'distance' },
  { label: '销量最高', value: 'sales' },
  { label: '评分最高', value: 'rating' },
  { label: '配送最快', value: 'speed' },
]

const SEARCH_HISTORY_KEY = 'search_history'
const MAX_HISTORY = 10

export default function UserHome() {
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [shops, setShops] = useState<ShopInfo[]>([])
  const [addresses, setAddresses] = useState<AddressInfo[]>([])
  const [selectedAddress, setSelectedAddress] = useState<AddressInfo | null>(null)
  const [sortBy, setSortBy] = useState('default')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const searchWrapperRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const isMobile = useIsMobile()

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target as Node)) {
        setShowHistory(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const history = localStorage.getItem(SEARCH_HISTORY_KEY)
    if (history) {
      setSearchHistory(JSON.parse(history))
    }
  }, [])

  const saveSearchHistory = (keyword: string) => {
    const trimmed = keyword.trim()
    if (!trimmed) {return}
    const history = searchHistory.filter((h) => h !== trimmed)
    const newHistory = [trimmed, ...history].slice(0, MAX_HISTORY)
    setSearchHistory(newHistory)
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(newHistory))
  }

  const clearSearchHistory = () => {
    setSearchHistory([])
    localStorage.removeItem(SEARCH_HISTORY_KEY)
  }

  const fetchShops = async (keyword?: string) => {
    try {
      setLoading(true)
      const res = await shopApi.listShops({ keyword, status: 1 })
      setShops(res.data.items)
    } catch (error) {
      console.error('获取商家列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAddresses = async () => {
    if (!isAuthenticated) {return}
    try {
      const res = await addressApi.getAddresses()
      setAddresses(res.data)
      const defaultAddr = res.data.find((a) => a.is_default === 1)
      setSelectedAddress(defaultAddr || res.data[0] || null)
    } catch (error) {
      console.error('获取地址失败', error)
    }
  }

  useEffect(() => {
    fetchShops()
    fetchAddresses()
  }, [])

  const handleSearch = (value: string) => {
    if (value.trim()) {
      saveSearchHistory(value.trim())
    }
    setSearchText(value)
    setSelectedCategory(value.trim() || null)
    fetchShops(value || undefined)
    setShowHistory(false)
  }

  const handleCategoryClick = (label: string) => {
    const keyword = label === '美食' ? '' : label
    setSelectedCategory(keyword)
    setSearchText(keyword)
    fetchShops(keyword || undefined)
  }

  const handleHistoryClick = (keyword: string) => {
    setSearchText(keyword)
    setSelectedCategory(keyword)
    fetchShops(keyword || undefined)
    setShowHistory(false)
  }

  const getSortedShops = () => {
    const sorted = [...shops]
    switch (sortBy) {
      case 'rating':
        sorted.sort((a, b) => b.rating - a.rating)
        break
      case 'sales':
        sorted.sort((a, b) => (b as any).monthly_sales - (a as any).monthly_sales)
        break
      default:
        break
    }
    return sorted
  }

  const renderSearchHistory = () => {
    if (!showHistory || searchHistory.length === 0) return null
    return (
      <div style={{
        position: 'absolute',
        top: '100%',
        left: 0,
        right: 0,
        background: '#fff',
        borderRadius: isMobile ? 12 : 8,
        boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        zIndex: 1000,
        padding: isMobile ? '8px 12px' : '12px 16px',
        maxHeight: 280,
        overflowY: 'auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <Text strong style={{ fontSize: 13, color: '#333' }}>
            <ClockCircleOutlined style={{ marginRight: 4 }} />搜索历史
          </Text>
          <span
            onClick={(e) => { e.stopPropagation(); clearSearchHistory() }}
            style={{ fontSize: 12, color: '#999', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 2 }}
          >
            <DeleteOutlined /> 清空
          </span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {searchHistory.map((keyword) => (
            <Tag
              key={keyword}
              style={{
                cursor: 'pointer', margin: 0, borderRadius: 14,
                padding: '2px 10px', fontSize: 12,
                background: '#f5f5f5', border: 'none', color: '#555',
              }}
              onClick={() => handleHistoryClick(keyword)}
            >
              {keyword}
            </Tag>
          ))}
        </div>
      </div>
    )
  }

  const renderShopCard = (shop: ShopInfo) => {
    const monthlySales = shop.monthly_sales || 0
    const deliveryFee = shop.delivery_fee || 0
    const minOrder = shop.min_order_amount || 0
    const deliveryTime = shop.delivery_time || ''
    let discountList: string[] = []
    try {
      discountList = shop.discounts ? JSON.parse(shop.discounts) : []
    } catch {
      discountList = []
    }

    if (isMobile) {
      return (
        <div
          className="mobile-card"
          key={shop.id}
          onClick={() => navigate(`/user/shop/${shop.id}`)}
          style={{ cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', gap: 10 }}>
            {shop.logo ? (
              <Image
                src={shop.logo}
                alt=""
                width={72}
                height={72}
                style={{ borderRadius: 8, flexShrink: 0, objectFit: 'cover' }}
                preview={false}
              />
            ) : (
              <div style={{
                width: 72, height: 72, background: '#fff7e6', borderRadius: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, fontSize: 28,
              }}>
                🏪
              </div>
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {shop.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <StarOutlined style={{ color: '#faad14', fontSize: 12 }} />
                <Text style={{ fontSize: 13, fontWeight: 600 }}>{shop.rating}</Text>
                <Text type="secondary" style={{ fontSize: 11 }}>月售{monthlySales}+</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: '#999' }}>
                <span>¥{minOrder}起送</span>
                <span>配送¥{deliveryFee}</span>
                <span><ClockCircleOutlined /> {deliveryTime}</span>
              </div>
              {discountList.length > 0 && (
                <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {discountList.slice(0, 2).map((d: string, i: number) => (
                    <Tag key={i} color="volcano" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}>{d}</Tag>
                  ))}
                </div>
              )}
              {shop.rating >= 4.5 && (
                <Tag color="orange" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', marginTop: 4 }}>口碑好店</Tag>
              )}
            </div>
          </div>
        </div>
      )
    }

    return (
      <List.Item key={shop.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/user/shop/${shop.id}`)}>
        <div style={{ display: 'flex', gap: 12, width: '100%' }}>
          {shop.logo ? (
            <Image src={shop.logo} alt="" width={80} height={80} style={{ borderRadius: 8, objectFit: 'cover' }} preview={false} />
          ) : (
            <div style={{
              width: 80, height: 80, background: '#fff7e6', borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32,
            }}>
              🏪
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <Title level={5} style={{ margin: '0 0 4px 0' }}>{shop.name}</Title>
            <Space size="small" style={{ marginBottom: 4 }}>
              <StarOutlined style={{ color: '#faad14' }} />
              <Text strong>{shop.rating}</Text>
              <Text type="secondary">月售{monthlySales}+</Text>
              <Text type="secondary">¥{minOrder}起送</Text>
              <Text type="secondary">配送¥{deliveryFee}</Text>
              <Text type="secondary"><ClockCircleOutlined /> {deliveryTime}</Text>
            </Space>
            <div>
              {discountList.length > 0 ? (
                discountList.slice(0, 3).map((d: string, i: number) => (
                  <Tag key={i} color="volcano" style={{ fontSize: 11 }}>{d}</Tag>
                ))
              ) : (
                <Tag color="orange">满减优惠</Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}><EnvironmentOutlined /> {shop.address}</Text>
          </div>
        </div>
      </List.Item>
    )
  }

  return (
    <div>
      {isMobile ? (
        <div>
          <div style={{ background: '#1890ff', padding: '12px 16px 16px' }}>
            <div
              style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10, color: '#fff', cursor: 'pointer' }}
              onClick={() => navigate('/user/addresses')}
            >
              <EnvironmentOutlined />
              <span style={{ fontSize: 14, fontWeight: 600, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedAddress ? selectedAddress.address : '请选择收货地址'}
              </span>
              <span style={{ fontSize: 10 }}>▼</span>
            </div>
            <div ref={searchWrapperRef} style={{ position: 'relative' }}>
              <Input
                size="large"
                placeholder="搜索商家或美食..."
                prefix={<SearchOutlined style={{ color: '#999' }} />}
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => { if (searchHistory.length > 0) setShowHistory(true) }}
                style={{ borderRadius: 20, borderColor: 'transparent' }}
                allowClear
              />
              {renderSearchHistory()}
            </div>
          </div>

          <div style={{ background: '#fff', padding: '12px 0' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 0 }}>
              {categoryItems.map((item) => (
                <div
                  key={item.label}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center',
                    padding: '6px 0', cursor: 'pointer', WebkitTapHighlightColor: 'transparent',
                  }}
                  onClick={() => handleCategoryClick(item.label)}
                >
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: selectedCategory === (item.label === '美食' ? '' : item.label) ? item.color : `${item.color}20`,
                    display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: 22, color: selectedCategory === (item.label === '美食' ? '' : item.label) ? '#fff' : item.color, marginBottom: 4,
                    transition: 'all 0.2s',
                  }}>
                    {item.icon}
                  </div>
                  <span style={{ fontSize: 11, color: selectedCategory === (item.label === '美食' ? '' : item.label) ? item.color : '#333', fontWeight: selectedCategory === (item.label === '美食' ? '' : item.label) ? 600 : 400 }}>
                    {item.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: '#fff', marginBottom: 8 }}>
            <Carousel autoplay dots={{ className: 'carousel-dots' }} style={{ borderRadius: 0 }}>
              <div style={{ height: 120, background: 'linear-gradient(135deg, #ff6b6b, #ee5a24)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', padding: '0 24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>新人专享红包</div>
                  <div style={{ fontSize: 14, marginTop: 4 }}>首单立减 最高减20元</div>
                </div>
              </div>
              <div style={{ height: 120, background: 'linear-gradient(135deg, #1890ff, #0984e3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', padding: '0 24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>准时达保障</div>
                  <div style={{ fontSize: 14, marginTop: 4 }}>超时赔付 放心下单</div>
                </div>
              </div>
              <div style={{ height: 120, background: 'linear-gradient(135deg, #00b894, #00cec9)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', padding: '0 24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>品质好店</div>
                  <div style={{ fontSize: 14, marginTop: 4 }}>精选商家 放心点餐</div>
                </div>
              </div>
            </Carousel>
          </div>

          <div style={{ background: '#fff', padding: '8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text strong style={{ fontSize: 15 }}>附近商家</Text>
            <Select
              value={sortBy}
              onChange={setSortBy}
              size="small"
              variant="borderless"
              style={{ width: 100 }}
              options={sortOptions}
            />
          </div>

          <Spin spinning={loading}>
            {shops.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Empty description="暂无商家信息" />
              </div>
            ) : (
              getSortedShops().map((shop) => renderShopCard(shop))
            )}
          </Spin>
        </div>
      ) : (
        <div>
          <div style={{
            background: 'linear-gradient(135deg, #1890ff, #0984e3)',
            padding: '24px', borderRadius: 12, marginBottom: 16,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <EnvironmentOutlined style={{ color: '#fff', fontSize: 18 }} />
              <Select
                value={selectedAddress?.id}
                onChange={(val) => {
                  const addr = addresses.find((a) => a.id === val)
                  setSelectedAddress(addr || null)
                }}
                style={{ minWidth: 300 }}
                placeholder="请选择收货地址"
              >
                {addresses.map((addr) => (
                  <Select.Option key={addr.id} value={addr.id}>
                    {addr.contact_name} - {addr.address}
                  </Select.Option>
                ))}
              </Select>
            </div>
            <div ref={searchWrapperRef} style={{ position: 'relative', maxWidth: 600 }}>
              <Input.Search
                size="large"
                placeholder="搜索商家或美食..."
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                onSearch={handleSearch}
                onFocus={() => { if (searchHistory.length > 0) setShowHistory(true) }}
                allowClear
              />
              {renderSearchHistory()}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 16 }}>
            {categoryItems.map((item) => (
              <div
                key={item.label}
                onClick={() => handleSearch(item.label === '美食' ? '' : item.label)}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  padding: '16px 8px', background: '#fff', borderRadius: 12,
                  cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s',
                }}
              >
                <div style={{
                  width: 52, height: 52, borderRadius: 14,
                  background: `${item.color}15`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  fontSize: 26, color: item.color, marginBottom: 8,
                }}>
                  {item.icon}
                </div>
                <span style={{ fontSize: 13, color: '#333' }}>{item.label}</span>
              </div>
            ))}
          </div>

          <div style={{ marginBottom: 16, borderRadius: 12, overflow: 'hidden' }}>
            <Carousel autoplay>
              <div style={{ height: 160, background: 'linear-gradient(135deg, #ff6b6b, #ee5a24)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>新人专享红包</div>
                  <div style={{ fontSize: 16, marginTop: 8 }}>首单立减 最高减20元</div>
                </div>
              </div>
              <div style={{ height: 160, background: 'linear-gradient(135deg, #1890ff, #0984e3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>准时达保障</div>
                  <div style={{ fontSize: 16, marginTop: 8 }}>超时赔付 放心下单</div>
                </div>
              </div>
              <div style={{ height: 160, background: 'linear-gradient(135deg, #00b894, #00cec9)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>品质好店</div>
                  <div style={{ fontSize: 16, marginTop: 8 }}>精选商家 放心点餐</div>
                </div>
              </div>
            </Carousel>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <Title level={4} style={{ margin: 0 }}>附近商家</Title>
            <Select value={sortBy} onChange={setSortBy} style={{ width: 120 }} options={sortOptions} />
          </div>

          <Spin spinning={loading}>
            <List
              locale={{ emptyText: <Empty description="暂无商家信息" /> }}
              dataSource={getSortedShops()}
              renderItem={renderShopCard}
            />
          </Spin>
        </div>
      )}
    </div>
  )
}
