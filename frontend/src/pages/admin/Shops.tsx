import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, message, Tag, Modal, Descriptions, Image, Input, Tabs, Form, InputNumber } from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined, StopOutlined, PlayCircleOutlined, EditOutlined, SearchOutlined } from '@ant-design/icons'
import { adminApi, ShopInfo } from '@/services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

const SHOP_STATUS_MAP: Record<number, { label: string; color: string }> = {
  0: { label: '待审核', color: 'orange' },
  1: { label: '已通过', color: 'green' },
  [-1]: { label: '已拒绝', color: 'red' },
  2: { label: '已禁用', color: 'default' },
}

const STATUS_TABS = [
  { key: 'all', label: '全部' },
  { key: '0', label: '待审核' },
  { key: '1', label: '已通过' },
  { key: '-1', label: '已拒绝' },
  { key: '2', label: '已禁用' },
]

export default function Shops() {
  const [shops, setShops] = useState<ShopInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [keyword, setKeyword] = useState('')
  const [detailVisible, setDetailVisible] = useState(false)
  const [editVisible, setEditVisible] = useState(false)
  const [selectedShop, setSelectedShop] = useState<ShopInfo | null>(null)
  const [editForm] = Form.useForm()
  const [editLoading, setEditLoading] = useState(false)
  const isMobile = useIsMobile()

  const fetchShops = async (p = page, ps = pageSize, status = statusFilter, kw = keyword) => {
    try {
      setLoading(true)
      const params: any = { page: p, page_size: ps }
      if (status !== 'all') {
        params.status = parseInt(status)
      }
      if (kw) {
        params.keyword = kw
      }
      const res = await adminApi.listAllShops(params)
      setShops(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取店铺列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShops()
  }, [page, pageSize, statusFilter])

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
    Modal.confirm({
      title: '确认拒绝',
      content: '确定要拒绝该店铺的入驻申请吗？',
      onOk: async () => {
        try {
          await adminApi.rejectShop(shopId)
          message.success('已拒绝')
          fetchShops()
        } catch (error) {
          console.error('拒绝失败:', error)
        }
      },
    })
  }

  const handleDisable = async (shopId: number) => {
    Modal.confirm({
      title: '确认禁用',
      content: '禁用后该店铺将无法正常营业，确定要禁用吗？',
      onOk: async () => {
        try {
          await adminApi.disableShop(shopId)
          message.success('店铺已禁用')
          fetchShops()
        } catch (error) {
          console.error('禁用失败:', error)
        }
      },
    })
  }

  const handleEnable = async (shopId: number) => {
    try {
      await adminApi.enableShop(shopId)
      message.success('店铺已启用')
      fetchShops()
    } catch (error) {
      console.error('启用失败:', error)
    }
  }

  const handleEdit = (shop: ShopInfo) => {
    setSelectedShop(shop)
    editForm.setFieldsValue({
      name: shop.name,
      address: shop.address,
      business_hours: shop.business_hours,
      notice: shop.notice,
      min_order_amount: shop.min_order_amount,
      delivery_fee: shop.delivery_fee,
      delivery_time: shop.delivery_time,
    })
    setEditVisible(true)
  }

  const handleEditSubmit = async () => {
    if (!selectedShop) {return}
    try {
      setEditLoading(true)
      const values = await editForm.validateFields()
      await adminApi.updateShop(selectedShop.id, values)
      message.success('更新成功')
      setEditVisible(false)
      fetchShops()
    } catch (error) {
      console.error('更新失败:', error)
    } finally {
      setEditLoading(false)
    }
  }

  const getStatusTag = (status: number) => {
    const info = SHOP_STATUS_MAP[status] || { label: '未知', color: 'default' }
    return <Tag color={info.color}>{info.label}</Tag>
  }

  const getActionButtons = (record: ShopInfo) => {
    const buttons = [
      <Button
        key="view"
        type="link"
        size="small"
        icon={<EyeOutlined />}
        onClick={() => {
          setSelectedShop(record)
          setDetailVisible(true)
        }}
      >
        查看
      </Button>,
    ]

    if (record.status === 0) {
      buttons.push(
        <Button key="approve" type="primary" size="small" icon={<CheckOutlined />} onClick={() => handleApprove(record.id)}>
          通过
        </Button>,
        <Button key="reject" danger size="small" icon={<CloseOutlined />} onClick={() => handleReject(record.id)}>
          拒绝
        </Button>,
      )
    }

    if (record.status === 1) {
      buttons.push(
        <Button key="edit" type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
          编辑
        </Button>,
        <Button key="disable" danger size="small" icon={<StopOutlined />} onClick={() => handleDisable(record.id)}>
          禁用
        </Button>,
      )
    }

    if (record.status === 2 || record.status === -1) {
      buttons.push(
        <Button key="enable" type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handleEnable(record.id)}>
          启用
        </Button>,
      )
    }

    return <Space size="small">{buttons}</Space>
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '店铺名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: 'Logo',
      dataIndex: 'logo',
      key: 'logo',
      width: 70,
      render: (logo: string) => logo ? <Image src={logo} width={40} height={40} style={{ borderRadius: 4 }} /> : '-',
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: number) => getStatusTag(status),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      width: 70,
    },
    {
      title: '营业时间',
      dataIndex: 'business_hours',
      key: 'business_hours',
      width: 120,
      render: (v: string) => v || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_: any, record: ShopInfo) => getActionButtons(record),
    },
  ]

  const renderMobileShops = () => {
    if (shops.length === 0) {
      return <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无店铺数据</div>
    }
    return shops.map((shop) => (
      <div className="mobile-card" key={shop.id}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {shop.logo ? (
            <Image src={shop.logo} width={48} height={48} style={{ borderRadius: 6, flexShrink: 0 }} />
          ) : (
            <div style={{
              width: 48, height: 48, background: '#f0f0f0', borderRadius: 6,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, color: '#999', fontSize: 12,
            }}>
              店铺
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{shop.name}</div>
            <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>{shop.address}</div>
            <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              {getStatusTag(shop.status)}
              <span style={{ fontSize: 12, color: '#999' }}>评分: {shop.rating}</span>
            </div>
          </div>
        </div>
        <div className="card-actions">
          {getActionButtons(shop)}
        </div>
      </div>
    ))
  }

  return (
    <Card title={isMobile ? undefined : '店铺管理'}>
      <div style={{ marginBottom: 16 }}>
        <Tabs
          activeKey={statusFilter}
          onChange={(key) => {
            setStatusFilter(key)
            setPage(1)
          }}
          items={STATUS_TABS.map((tab) => ({
            key: tab.key,
            label: tab.label,
          }))}
          size="small"
          style={{ marginBottom: 8 }}
        />
        <Input.Search
          placeholder="搜索店铺名称"
          allowClear
          onSearch={(value) => {
            setKeyword(value)
            setPage(1)
            fetchShops(1, pageSize, statusFilter, value)
          }}
          style={{ maxWidth: 300 }}
          prefix={<SearchOutlined />}
        />
      </div>

      {isMobile ? renderMobileShops() : (
        <Table
          columns={columns}
          dataSource={shops}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
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
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="店铺ID">{selectedShop.id}</Descriptions.Item>
            <Descriptions.Item label="店铺名称">{selectedShop.name}</Descriptions.Item>
            <Descriptions.Item label="店铺Logo">
              {selectedShop.logo ? <Image src={selectedShop.logo} width={200} /> : '未设置'}
            </Descriptions.Item>
            <Descriptions.Item label="店铺地址">{selectedShop.address}</Descriptions.Item>
            <Descriptions.Item label="营业时间">{selectedShop.business_hours || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="店铺公告">{selectedShop.notice || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="店铺评分">{selectedShop.rating}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(selectedShop.status)}</Descriptions.Item>
            <Descriptions.Item label="起送金额">¥{selectedShop.min_order_amount}</Descriptions.Item>
            <Descriptions.Item label="配送费">¥{selectedShop.delivery_fee}</Descriptions.Item>
            <Descriptions.Item label="配送时间">{selectedShop.delivery_time}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedShop.created_at ? new Date(selectedShop.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{selectedShop.updated_at ? new Date(selectedShop.updated_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal
        title="编辑店铺"
        open={editVisible}
        onCancel={() => setEditVisible(false)}
        onOk={handleEditSubmit}
        confirmLoading={editLoading}
        width={isMobile ? undefined : 500}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="店铺名称" rules={[{ required: true, message: '请输入店铺名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="address" label="店铺地址" rules={[{ required: true, message: '请输入店铺地址' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="business_hours" label="营业时间">
            <Input placeholder="例如：09:00-22:00" />
          </Form.Item>
          <Form.Item name="notice" label="店铺公告">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="min_order_amount" label="起送金额">
            <InputNumber min={0} precision={2} addonAfter="元" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="delivery_fee" label="配送费">
            <InputNumber min={0} precision={2} addonAfter="元" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="delivery_time" label="配送时间">
            <Input placeholder="例如：30分钟" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
