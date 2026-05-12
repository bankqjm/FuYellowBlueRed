
import { Input, List, Card, Typography, Space, Empty, Spin, Tag, Image } from 'antd'
import { SearchOutlined, EnvironmentOutlined, StarOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { shopApi, ShopInfo } from '../../services/shop'

const { Title, Text } = Typography

export default function UserHome() {
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [shops, setShops] = useState<ShopInfo[]>([])
  const navigate = useNavigate()

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

  useEffect(() => {
    fetchShops()
  }, [])

  const getStatusText = (status: number) => {
    switch (status) {
      case 0:
        return <Tag color="orange">待审核</Tag>
      case 1:
        return <Tag color="green">营业中</Tag>
      case 2:
        return <Tag color="blue">休息中</Tag>
      default:
        return <Tag>未知</Tag>
    }
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Input
          size="large"
          placeholder="搜索商家..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value)
            fetchShops(e.target.value)
          }}
        />
      </Card>

      <Spin spinning={loading}>
        <List
          locale={{ emptyText: <Empty description="暂无商家信息" /> }}
          renderItem={(shop) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => navigate(`/user/shop/${shop.id}`)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    {shop.logo ? (
                      <Image src={shop.logo} alt="" width={60} height={60} />
                    ) : (
                      <div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ color: '#999' }}>店铺</span>
                      </div>
                    )}
                    <div style={{ flex: 1 }}>
                      <Title level={5} style={{ margin: 0 }}>{shop.name}</Title>
                      <Space>
                        {getStatusText(shop.status)}
                        <Text><StarOutlined style={{ color: '#faad14' }} /> {shop.rating}</Text>
                      </Space>
                    </div>
                  </Space>
                  <Text><EnvironmentOutlined /> {shop.address}</Text>
                </Space>
              </Card>
            </List.Item>
          )}
          dataSource={shops}
        />
      </Spin>
    </div>
  )
}

