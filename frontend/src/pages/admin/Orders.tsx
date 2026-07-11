
import { useState, useEffect } from 'react'
import { Card, Table, Tabs, Tag, Space, Button, Modal, Descriptions, Empty, Spin, Typography, Input, message } from 'antd'
import { EyeOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons'
import { adminApi } from '@/services/shop'
import type { OrderInfo } from '@/services/shop'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

const statusOptions = [
  { label: '全部', value: '' },
  { label: '待支付', value: 'PENDING_PAYMENT' },
  { label: '待接单', value: 'PENDING_ACCEPT' },
  { label: '备餐中', value: 'ACCEPTED' },
  { label: '待取餐', value: 'READY' },
  { label: '配送中', value: 'DELIVERING' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '已取消', value: 'CANCELLED' },
]

/** Mask phone number for display: 138****5678 */
function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) {return phone}
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

export default function AdminOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<OrderInfo | null>(null)
  const isMobile = useIsMobile()

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const res = await adminApi.listAdminOrders({
        status: status || undefined,
        page,
        page_size: 20,
        keyword: keyword || undefined,
      })
      setOrders(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取订单列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [status, page, keyword])

  const getStatusText = (status: string) => {
    const statusMap: Record<string, { text: string; color: string }> = {
      PENDING_PAYMENT: { text: '待支付', color: 'blue' },
      PENDING_ACCEPT: { text: '待接单', color: 'orange' },
      ACCEPTED: { text: '备餐中', color: 'cyan' },
      READY: { text: '待取餐', color: 'purple' },
      DELIVERING: { text: '配送中', color: 'gold' },
      COMPLETED: { text: '已完成', color: 'green' },
      CANCELLED: { text: '已取消', color: 'default' },
    }
    return statusMap[status] || { text: status, color: 'default' }
  }

  const handleSearch = () => {
    setKeyword(searchInput)
    setPage(1)
  }

  const handleExportCSV = () => {
    if (orders.length === 0) {
      message.warning('暂无数据可导出')
      return
    }

    const headers = ['订单号', '商家', '金额', '状态', '下单人', '创建时间']
    const rows = orders.map((order) => [
      order.order_no,
      order.shop_name || '',
      order.total_amount.toFixed(2),
      getStatusText(order.status).text,
      order.user_nickname || '',
      order.created_at ? new Date(order.created_at).toLocaleString() : '',
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n')

    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `orders_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    message.success('导出成功')
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 200,
    },
    {
      title: '商家',
      dataIndex: 'shop_name',
      key: 'shop_name',
    },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number) => `¥${amount.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const info = getStatusText(status)
        return <Tag color={info.color}>{info.text}</Tag>
      },
    },
    {
      title: '下单人',
      key: 'user_nickname',
      render: (_: any, record: OrderInfo) => record.user_nickname || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => (time ? new Date(time).toLocaleString() : '-'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: OrderInfo) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => {
            setSelectedOrder(record)
            setDetailVisible(true)
          }}
        >
          查看详情
        </Button>
      ),
    },
  ]

  const tabItems = statusOptions.map((opt) => ({
    key: opt.value,
    label: opt.label,
  }))

  if (loading && orders.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Card>
      <Title level={4}>订单管理</Title>

      <Tabs
        activeKey={status}
        onChange={(key) => {
          setStatus(key)
          setPage(1)
        }}
        items={tabItems}
        style={{ marginBottom: 16 }}
      />

      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="搜索订单号/商家名"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
          style={{ width: isMobile ? '100%' : 300 }}
          allowClear
          onClear={() => {
            setSearchInput('')
            setKeyword('')
            setPage(1)
          }}
        />
        <Button icon={<DownloadOutlined />} onClick={handleExportCSV}>
          导出 Excel
        </Button>
      </Space>

      {orders.length === 0 ? (
        <Empty description="暂无订单" />
      ) : (
        <>
          <Table
            columns={columns}
            dataSource={orders}
            rowKey="id"
            loading={loading}
            scroll={isMobile ? { x: 800 } : undefined}
            pagination={{
              current: page,
              total,
              pageSize: 20,
              onChange: setPage,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        </>
      )}

      <Modal
        title="订单详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={isMobile ? undefined : 600}
      >
        {selectedOrder && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="订单号">{selectedOrder.order_no}</Descriptions.Item>
            <Descriptions.Item label="商家">{selectedOrder.shop_name}</Descriptions.Item>
            {selectedOrder.user_nickname && (
              <Descriptions.Item label="下单用户">
                {selectedOrder.user_nickname}
                {selectedOrder.user_phone && ` (${maskPhone(selectedOrder.user_phone)})`}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="订单金额">
              ¥{selectedOrder.total_amount.toFixed(2)}
            </Descriptions.Item>
            <Descriptions.Item label="配送费">¥{selectedOrder.delivery_fee.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="收货地址">{selectedOrder.address}</Descriptions.Item>
            <Descriptions.Item label="联系电话">{maskPhone(selectedOrder.phone)}</Descriptions.Item>
            <Descriptions.Item label="订单状态">
              <Tag color={getStatusText(selectedOrder.status).color}>
                {getStatusText(selectedOrder.status).text}
              </Tag>
            </Descriptions.Item>
            {selectedOrder.remark && (
              <Descriptions.Item label="备注">{selectedOrder.remark}</Descriptions.Item>
            )}
            {selectedOrder.reject_reason && (
              <Descriptions.Item label="拒单原因">
                <Text type="danger">{selectedOrder.reject_reason}</Text>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="创建时间">
              {selectedOrder.created_at ? new Date(selectedOrder.created_at).toLocaleString() : '-'}
            </Descriptions.Item>
            {selectedOrder.items && selectedOrder.items.length > 0 && (
              <Descriptions.Item label="商品明细">
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {selectedOrder.items.map((item) => (
                    <li key={item.id}>
                      {item.product_name} × {item.quantity} - ¥
                      {(item.price * item.quantity).toFixed(2)}
                    </li>
                  ))}
                </ul>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </Card>
  )
}
