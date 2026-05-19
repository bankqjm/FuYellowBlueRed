
import { useState, useEffect } from 'react'
import { Card, Table, Tabs, Tag, Space, Button, Modal, Descriptions, Empty, Spin, Typography } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
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

export default function AdminOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<OrderInfo | null>(null)
  const isMobile = useIsMobile()

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const res = await adminApi.listAdminOrders({ status: status || undefined, page, page_size: 20 })
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
  }, [status, page])

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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-',
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

      {orders.length === 0 ? (
        <Empty description="暂无订单" />
      ) : (
        <>
          <Table
            columns={columns}
            dataSource={orders}
            rowKey="id"
            loading={loading}
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
            <Descriptions.Item label="订单金额">¥{selectedOrder.total_amount.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="配送费">¥{selectedOrder.delivery_fee.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="收货地址">{selectedOrder.address}</Descriptions.Item>
            <Descriptions.Item label="联系电话">{selectedOrder.phone}</Descriptions.Item>
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
                      {item.product_name} × {item.quantity} - ¥{(item.price * item.quantity).toFixed(2)}
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
