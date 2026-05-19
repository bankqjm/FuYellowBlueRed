
import { useState, useEffect } from 'react'
import { Card, Typography, List, Spin, Empty, Button, message, Tag, Tabs, Badge } from 'antd'
import { TicketOutlined, CheckCircleOutlined, GiftOutlined } from '@ant-design/icons'
import { couponsApi, CouponInfo, UserCouponInfo } from '../../services/coupons'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography

export default function Coupons() {
  const [loading, setLoading] = useState(true)
  const [availableCoupons, setAvailableCoupons] = useState<CouponInfo[]>([])
  const [myCoupons, setMyCoupons] = useState<UserCouponInfo[]>([])
  const [activeTab, setActiveTab] = useState('available')
  const navigate = useNavigate()

  const fetchAvailableCoupons = async () => {
    try {
      setLoading(true)
      const res = await couponsApi.listAvailableCoupons({ page: 1, page_size: 50 })
      setAvailableCoupons(res.data.items)
    } catch (error) {
      console.error('获取优惠券失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMyCoupons = async (status?: string) => {
    try {
      setLoading(true)
      const res = await couponsApi.listMyCoupons({ status, page: 1, page_size: 50 })
      setMyCoupons(res.data.items)
    } catch (error) {
      console.error('获取我的优惠券失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAvailableCoupons()
    fetchMyCoupons()
  }, [])

  const handleClaim = async (couponId: number) => {
    try {
      await couponsApi.claimCoupon(couponId)
      message.success('领取成功')
      fetchAvailableCoupons()
      fetchMyCoupons('UNUSED')
      setActiveTab('my')
    } catch (error: any) {
      message.error(error?.response?.data?.message || '领取失败')
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  const isExpired = (coupon: CouponInfo) => {
    return new Date(coupon.valid_until) < new Date()
  }

  if (loading && availableCoupons.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4} style={{ margin: 0 }}>
          <TicketOutlined style={{ marginRight: 8 }} />
          优惠券
        </Title>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            if (key === 'available') {
              fetchAvailableCoupons()
            } else {
              fetchMyCoupons(key === 'my' ? 'UNUSED' : undefined)
            }
          }}
          items={[
            {
              key: 'available',
              label: (
                <span>
                  <GiftOutlined />
                  领券中心
                </span>
              ),
            },
            {
              key: 'my',
              label: (
                <Badge count={myCoupons.filter((c) => c.status === 'UNUSED').length} offset={[10, 0]}>
                  <span>我的优惠券</span>
                </Badge>
              ),
            },
          ]}
        />

        {activeTab === 'available' && (
          <>
            {availableCoupons.length === 0 ? (
              <Empty description="暂无可领取的优惠券" />
            ) : (
              <List
                dataSource={availableCoupons}
                renderItem={(coupon) => (
                  <List.Item
                    actions={[
                      coupon.is_claimed ? (
                        <Tag color="green" icon={<CheckCircleOutlined />}>已领取</Tag>
                      ) : (
                        <Button
                          type="primary"
                          size="small"
                          disabled={coupon.remain_count <= 0 || isExpired(coupon)}
                          onClick={() => handleClaim(coupon.id)}
                        >
                          {coupon.remain_count <= 0 ? '已抢光' : '立即领取'}
                        </Button>
                      ),
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 24, color: '#ff4d4f', fontWeight: 700 }}>
                            ¥{coupon.discount_amount.toFixed(0)}
                          </span>
                          <span style={{ fontSize: 14, color: '#666' }}>
                            {coupon.name}
                          </span>
                        </div>
                      }
                      description={
                        <div>
                          <Text type="secondary">
                            满{coupon.min_order_amount.toFixed(0)}元可用
                          </Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            有效期：{formatDate(coupon.valid_from)} - {formatDate(coupon.valid_until)}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 12, marginLeft: 16 }}>
                            剩余 {coupon.remain_count}/{coupon.total_count}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </>
        )}

        {activeTab === 'my' && (
          <>
            {myCoupons.length === 0 ? (
              <Empty description="暂无优惠券">
                <Button type="primary" onClick={() => setActiveTab('available')}>
                  去领券
                </Button>
              </Empty>
            ) : (
              <List
                dataSource={myCoupons}
                renderItem={(item) => {
                  const coupon = item.coupon
                  const expired = new Date(coupon.valid_until) < new Date()
                  const used = item.status === 'USED'
                  return (
                    <List.Item>
                      <List.Item.Meta
                        title={
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 24, color: expired || used ? '#999' : '#ff4d4f', fontWeight: 700 }}>
                              ¥{coupon.discount_amount.toFixed(0)}
                            </span>
                            <span style={{ fontSize: 14, color: expired || used ? '#999' : '#666' }}>
                              {coupon.name}
                            </span>
                          </div>
                        }
                        description={
                          <div>
                            <Text type="secondary">
                              满{coupon.min_order_amount.toFixed(0)}元可用
                            </Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              有效期至：{formatDate(coupon.valid_until)}
                            </Text>
                          </div>
                        }
                      />
                      {used ? (
                        <Tag color="default">已使用</Tag>
                      ) : expired ? (
                        <Tag color="default">已过期</Tag>
                      ) : (
                        <Button
                          type="primary"
                          size="small"
                          onClick={() => navigate('/user/home')}
                        >
                          去使用
                        </Button>
                      )}
                    </List.Item>
                  )
                }}
              />
            )}
          </>
        )}
      </Card>
    </div>
  )
}
