
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Typography, List, Spin, Empty, Image, Button, message, Tag } from 'antd'
import { HeartOutlined, StarFilled, ShopOutlined } from '@ant-design/icons'
import { favoritesApi, FavoriteShop } from '../../services/favorites'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

export default function Favorites() {
  const [loading, setLoading] = useState(true)
  const [favorites, setFavorites] = useState<FavoriteShop[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const navigate = useNavigate()
  const isMobile = useIsMobile()

  const fetchFavorites = async () => {
    try {
      setLoading(true)
      const res = await favoritesApi.listFavorites({ page, page_size: 20 })
      setFavorites(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取收藏列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFavorites()
  }, [page])

  const handleRemove = async (shopId: number) => {
    try {
      await favoritesApi.removeFavorite(shopId)
      message.success('已取消收藏')
      fetchFavorites()
    } catch (error) {
      console.error('取消收藏失败', error)
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
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>
            <HeartOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
            我的收藏
          </Title>
          <Text type="secondary">共 {total} 家</Text>
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        {favorites.length === 0 ? (
          <Empty
            image={<ShopOutlined style={{ fontSize: 64, color: '#ccc' }} />}
            description="暂无收藏商家"
          >
            <Button type="primary" onClick={() => navigate('/user/home')}>
              去逛逛
            </Button>
          </Empty>
        ) : (
          <List
            dataSource={favorites}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button
                    type="text"
                    danger
                    key="remove"
                    onClick={() => handleRemove(item.shop_id)}
                  >
                    取消收藏
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    item.shop_image ? (
                      <Image
                        src={item.shop_image}
                        width={80}
                        height={80}
                        style={{ borderRadius: 8, objectFit: 'cover' }}
                      />
                    ) : (
                      <div
                        style={{
                          width: 80,
                          height: 80,
                          borderRadius: 8,
                          background: '#f5f5f5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <ShopOutlined style={{ fontSize: 32, color: '#ccc' }} />
                      </div>
                    )
                  }
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>{item.shop_name}</span>
                      {item.shop_rating && (
                        <Tag color="gold" icon={<StarFilled />}>
                          {item.shop_rating.toFixed(1)}
                        </Tag>
                      )}
                    </div>
                  }
                  description={
                    <div>
                      <Text type="secondary">
                        月售 {item.monthly_sales || 0} 单
                        {item.delivery_time && ` · 约${item.delivery_time}分钟`}
                      </Text>
                      <br />
                      <Text type="secondary">
                        ¥{item.min_order_amount?.toFixed(2) || '0.00'}起送
                      </Text>
                    </div>
                  }
                  onClick={() => navigate(`/user/shop/${item.shop_id}`)}
                  style={{ cursor: 'pointer' }}
                />
              </List.Item>
            )}
          />
        )}

        {total > 20 && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Button onClick={() => setPage((p) => p + 1)}>加载更多</Button>
          </div>
        )}
      </Card>
    </div>
  )
}
