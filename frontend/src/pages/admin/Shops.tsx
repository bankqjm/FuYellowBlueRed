import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, message, Tag, Modal, Descriptions, Image } from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { adminApi, ShopInfo } from '@/services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

export default function Shops() {
  const [shops, setShops] = useState<ShopInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedShop, setSelectedShop] = useState<ShopInfo | null>(null)
  const isMobile = useIsMobile()

  const fetchShops = async () => {
    try {
      setLoading(true)
      const res = await adminApi.listPendingShops()
      setShops(res.data.items)
    } catch (error) {
      console.error('获取店铺列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShops()
  }, [])

  const handleApprove = async (shopId: number) => {
    try {
      await adminApi.approveShop(shopId)
      message.success('审核通过')
      fetchShops()
    } catch (error) {
      console.error('审核失败:', error)
    }
  }

  const handleReject = async (shopId: number) => {
    try {
      await adminApi.rejectShop(shopId)
      message.success('已拒绝')
      fetchShops()
    } catch (error) {
      console.error('拒绝失败:', error)
    }
  }

  const getStatusText = (status: number) => {
    switch (status) {
      case 0:
        return <Tag color="orange">待审核</Tag>
      case 1:
        return <Tag color="green">已通过</Tag>
      case -1:
        return <Tag color="red">已拒绝</Tag>
      default:
        return <Tag>未知</Tag>
    }
  }

  const columns = [
    {
      title: '店铺名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '店铺Logo',
      dataIndex: 'logo',
      key: 'logo',
      render: (logo: string) => logo ? <Image src={logo} width={60} height={60} /> : '-',
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => getStatusText(status),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ShopInfo) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedShop(record)
              setDetailVisible(true)
            }}
          >
            查看
          </Button>
          {record.status === 0 && (
            <>
              <Button
                type="primary"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleApprove(record.id)}
              >
                通过
              </Button>
              <Button
                danger
                size="small"
                icon={<CloseOutlined />}
                onClick={() => handleReject(record.id)}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  const renderMobileShops = () => {
    if (shops.length === 0) {
      return <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无待审核店铺</div>
    }
    return shops.map(shop => (
      <div className="mobile-card" key={shop.id}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {shop.logo ? (
            <Image src={shop.logo} width={48} height={48} style={{ borderRadius: 6, flexShrink: 0 }} />
          ) : (
            <div style={{
              width: 48, height: 48, background: '#f0f0f0', borderRadius: 6,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, color: '#999', fontSize: 12
            }}>
              店铺
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{shop.name}</div>
            <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>{shop.address}</div>
            <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              {getStatusText(shop.status)}
              <span style={{ fontSize: 12, color: '#999' }}>评分: {shop.rating}</span>
            </div>
          </div>
        </div>
        <div className="card-actions">
          <Button size="small" icon={<EyeOutlined />} onClick={() => {
            setSelectedShop(shop)
            setDetailVisible(true)
          }}>查看</Button>
          {shop.status === 0 && (
            <>
              <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => handleApprove(shop.id)}>通过</Button>
              <Button danger size="small" icon={<CloseOutlined />} onClick={() => handleReject(shop.id)}>拒绝</Button>
            </>
          )}
        </div>
      </div>
    ))
  }

  return (
    <Card title={isMobile ? undefined : '店铺审核'}>
      {isMobile ? renderMobileShops() : (
        <Table
          columns={columns}
          dataSource={shops}
          rowKey="id"
          loading={loading}
        />
      )}
      <Modal
        title="店铺详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={isMobile ? undefined : 600}
      >
        {selectedShop && (
          <Descriptions column={1}>
            <Descriptions.Item label="店铺名称">{selectedShop.name}</Descriptions.Item>
            <Descriptions.Item label="店铺Logo">
              {selectedShop.logo ? (
                <Image src={selectedShop.logo} width={200} />
              ) : (
                '未设置'
              )}
            </Descriptions.Item>
            <Descriptions.Item label="店铺地址">{selectedShop.address}</Descriptions.Item>
            <Descriptions.Item label="营业时间">{selectedShop.business_hours || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="店铺公告">{selectedShop.notice || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="店铺评分">{selectedShop.rating}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusText(selectedShop.status)}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedShop.created_at}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  )
}
