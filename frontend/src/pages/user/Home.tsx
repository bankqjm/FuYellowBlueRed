
import { Input, List, Card, Typography, Space, Empty, Spin, Tag, Image } from 'antd'
import { SearchOutlined, EnvironmentOutlined, StarOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { shopApi, ShopInfo } from '../../services/shop'

const { Title, Text } = Typography

export default function UserHome() {
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [shops, setShops] = useState&lt;ShopInfo[]&gt;([])
  const navigate = useNavigate()

  const fetchShops = async (keyword?: string) =&gt; {
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

  useEffect(() =&gt; {
    fetchShops()
  }, [])

  const getStatusText = (status: number) =&gt; {
    switch (status) {
      case 0:
        return &lt;Tag color="orange"&gt;待审核&lt;/Tag&gt;
      case 1:
        return &lt;Tag color="green"&gt;营业中&lt;/Tag&gt;
      case 2:
        return &lt;Tag color="blue"&gt;休息中&lt;/Tag&gt;
      default:
        return &lt;Tag&gt;未知&lt;/Tag&gt;
    }
  }

  return (
    &lt;div&gt;
      &lt;Card style={{ marginBottom: 16 }}&gt;
        &lt;Input
          size="large"
          placeholder="搜索商家..."
          prefix={&lt;SearchOutlined /&gt;}
          value={searchText}
          onChange={(e) =&gt; {
            setSearchText(e.target.value)
            fetchShops(e.target.value)
          }}
        /&gt;
      &lt;/Card&gt;

      &lt;Spin spinning={loading}&gt;
        &lt;List
          locale={{ emptyText: &lt;Empty description="暂无商家信息" /&gt; }}
          renderItem={(shop) =&gt; (
            &lt;List.Item&gt;
              &lt;Card
                hoverable
                onClick={() =&gt; navigate(`/user/shop/${shop.id}`)}
                style={{ width: '100%' }}
              &gt;
                &lt;Space direction="vertical" size="small" style={{ width: '100%' }}&gt;
                  &lt;Space&gt;
                    {shop.logo ? (
                      &lt;Image src={shop.logo} alt="" width={60} height={60} /&gt;
                    ) : (
                      &lt;div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}&gt;
                        &lt;span style={{ color: '#999' }}&gt;店铺&lt;/span&gt;
                      &lt;/div&gt;
                    )}
                    &lt;div style={{ flex: 1 }}&gt;
                      &lt;Title level={5} style={{ margin: 0 }}&gt;{shop.name}&lt;/Title&gt;
                      &lt;Space&gt;
                        {getStatusText(shop.status)}
                        &lt;Text&gt;&lt;StarOutlined style={{ color: '#faad14' }} /&gt; {shop.rating}&lt;/Text&gt;
                      &lt;/Space&gt;
                    &lt;/div&gt;
                  &lt;/Space&gt;
                  &lt;Text&gt;&lt;EnvironmentOutlined /&gt; {shop.address}&lt;/Text&gt;
                &lt;/Space&gt;
              &lt;/Card&gt;
            &lt;/List.Item&gt;
          )}
          dataSource={shops}
        /&gt;
      &lt;/Spin&gt;
    &lt;/div&gt;
  )
}

