import { useState, useEffect } from 'react'
import { Card, Typography, Table, Button, Tag, Space, message, Modal, Form, Input, InputNumber, DatePicker, Popconfirm, Select } from 'antd'
import { PlusOutlined, CheckOutlined, StopOutlined } from '@ant-design/icons'
import api from '../../services/api'
import type { ColumnsType } from 'antd/es/table'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

interface CouponRecord {
  id: number
  name: string
  code: string
  description?: string
  discount_amount: number
  min_order_amount: number
  total_count: number
  remaining_count: number
  valid_from: string
  valid_until: string
  status: string
  created_at?: string
}

const STATUS_MAP: Record<string, { text: string; color: string }> = {
  ACTIVE: { text: '已上架', color: 'green' },
  INACTIVE: { text: '已下架', color: 'red' },
  EXPIRED: { text: '已过期', color: 'default' },
}

export default function Coupons() {
  const [loading, setLoading] = useState(false)
  const [coupons, setCoupons] = useState<CouponRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [form] = Form.useForm()
  const isMobile = useIsMobile()

  const fetchCoupons = async () => {
    try {
      setLoading(true)
      const params: Record<string, any> = { page, page_size: pageSize }
      if (statusFilter) { params.status = statusFilter }
      const res = await api.get<{ items: CouponRecord[]; total: number }>('/coupons/admin/list', { params })
      setCoupons(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取优惠券列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCoupons()
  }, [page, pageSize, statusFilter])

  const handleUpdateStatus = async (couponId: number, newStatus: string) => {
    try {
      await api.put(`/coupons/admin/${couponId}/status`, null, { params: { status: newStatus } })
      message.success(newStatus === 'ACTIVE' ? '上架成功' : '下架成功')
      fetchCoupons()
    } catch (error) {
      console.error('更新状态失败', error)
    }
  }

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      setCreateLoading(true)
      await api.post('/coupons/admin/create', {
        ...values,
        valid_from: values.valid_range[0].toISOString(),
        valid_until: values.valid_range[1].toISOString(),
      })
      message.success('创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchCoupons()
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'errorFields' in error) {
        return  // 表单验证错误，不需要处理
      }
      message.error('操作失败')
    } finally {
      setCreateLoading(false)
    }
  }

  const formatTime = (time: string) => time ? new Date(time).toLocaleString() : '-'

  const getStatusTag = (status: string) => {
    const info = STATUS_MAP[status] || { text: status, color: 'default' }
    return <Tag color={info.color}>{info.text}</Tag>
  }

  const columns: ColumnsType<CouponRecord> = [
    {
      title: '名称',
      dataIndex: 'name',
      width: 140,
    },
    {
      title: '优惠码',
      dataIndex: 'code',
      width: 120,
    },
    {
      title: '优惠金额',
      dataIndex: 'discount_amount',
      width: 100,
      render: (val: number) => `¥${val}`,
    },
    {
      title: '最低消费',
      dataIndex: 'min_order_amount',
      width: 100,
      render: (val: number) => `¥${val}`,
    },
    {
      title: '总量/剩余',
      width: 110,
      render: (_, record) => `${record.total_count} / ${record.remaining_count}`,
    },
    {
      title: '有效期',
      width: 200,
      render: (_, record) => (
        <span style={{ fontSize: 12 }}>
          {formatTime(record.valid_from)} ~ {formatTime(record.valid_until)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <Space>
          {record.status === 'ACTIVE' ? (
            <Popconfirm title="确定下架该优惠券？" onConfirm={() => handleUpdateStatus(record.id, 'INACTIVE')}>
              <Button size="small" danger icon={<StopOutlined />}>下架</Button>
            </Popconfirm>
          ) : record.status !== 'EXPIRED' ? (
            <Popconfirm title="确定上架该优惠券？" onConfirm={() => handleUpdateStatus(record.id, 'ACTIVE')}>
              <Button size="small" type="primary" icon={<CheckOutlined />}>上架</Button>
            </Popconfirm>
          ) : null}
        </Space>
      ),
    },
  ]

  const renderMobileCoupons = () => {
    if (coupons.length === 0) {
      return <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无优惠券数据</div>
    }
    return coupons.map((coupon) => (
      <div className="mobile-card" key={coupon.id}>
        <div className="card-row">
          <span className="label">名称</span>
          <span className="value">{coupon.name}</span>
        </div>
        <div className="card-row">
          <span className="label">优惠码</span>
          <span className="value" style={{ fontFamily: 'monospace' }}>{coupon.code}</span>
        </div>
        <div className="card-row">
          <span className="label">优惠金额</span>
          <span className="value" style={{ color: '#f50', fontWeight: 600 }}>¥{coupon.discount_amount}</span>
        </div>
        <div className="card-row">
          <span className="label">最低消费</span>
          <span className="value">¥{coupon.min_order_amount}</span>
        </div>
        <div className="card-row">
          <span className="label">总量/剩余</span>
          <span className="value">{coupon.total_count} / {coupon.remaining_count}</span>
        </div>
        <div className="card-row">
          <span className="label">有效期</span>
          <span className="value" style={{ fontSize: 11 }}>
            {formatTime(coupon.valid_from)} ~ {formatTime(coupon.valid_until)}
          </span>
        </div>
        <div className="card-row">
          <span className="label">状态</span>
          <span className="value">{getStatusTag(coupon.status)}</span>
        </div>
        <div className="card-actions">
          {coupon.status === 'ACTIVE' ? (
            <Popconfirm title="确定下架该优惠券？" onConfirm={() => handleUpdateStatus(coupon.id, 'INACTIVE')}>
              <Button size="small" danger icon={<StopOutlined />}>下架</Button>
            </Popconfirm>
          ) : coupon.status !== 'EXPIRED' ? (
            <Popconfirm title="确定上架该优惠券？" onConfirm={() => handleUpdateStatus(coupon.id, 'ACTIVE')}>
              <Button size="small" type="primary" icon={<CheckOutlined />}>上架</Button>
            </Popconfirm>
          ) : null}
        </div>
      </div>
    ))
  }

  return (
    <div>
      <Card>
        <Title level={4}>优惠券管理</Title>
      </Card>

      <Card style={{ marginTop: isMobile ? 8 : 16 }}>
        <Space style={{ marginBottom: 16, flexWrap: 'wrap' }} direction={isMobile ? 'vertical' : 'horizontal'}>
          <Select
            placeholder="筛选状态"
            value={statusFilter || undefined}
            onChange={(value) => setStatusFilter(value || '')}
            style={{ width: isMobile ? '100%' : 140 }}
            allowClear
          >
            <Select.Option value="ACTIVE">已上架</Select.Option>
            <Select.Option value="INACTIVE">已下架</Select.Option>
            <Select.Option value="EXPIRED">已过期</Select.Option>
          </Select>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建优惠券
          </Button>
        </Space>

        {isMobile ? renderMobileCoupons() : (
          <Table
            columns={columns}
            dataSource={coupons}
            rowKey="id"
            loading={loading}
            scroll={{ x: 980 }}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (t) => `共 ${t} 条`,
              onChange: (p, ps) => {
                setPage(p)
                setPageSize(ps || 20)
              },
            }}
          />
        )}
      </Card>

      <Modal
        title="创建优惠券"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        confirmLoading={createLoading}
        okText="创建"
        cancelText="取消"
        width={isMobile ? undefined : 520}
      >
        <Form form={form} layout="vertical" initialValues={{ min_order_amount: 0 }}>
          <Form.Item name="name" label="优惠券名称" rules={[{ required: true, message: '请输入优惠券名称' }]}>
            <Input placeholder="请输入优惠券名称" />
          </Form.Item>
          <Form.Item name="code" label="优惠码" rules={[{ required: true, message: '请输入优惠码' }]}>
            <Input placeholder="请输入优惠码" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入描述（选填）" />
          </Form.Item>
          <Space style={{ width: '100%' }} direction={isMobile ? 'vertical' : 'horizontal'} size="middle">
            <Form.Item name="discount_amount" label="优惠金额" rules={[{ required: true, message: '请输入优惠金额' }]} style={{ width: isMobile ? '100%' : 240 }}>
              <InputNumber min={0.01} precision={2} style={{ width: '100%' }} placeholder="优惠金额" />
            </Form.Item>
            <Form.Item name="min_order_amount" label="最低消费" rules={[{ required: true, message: '请输入最低消费金额' }]} style={{ width: isMobile ? '100%' : 240 }}>
              <InputNumber min={0} precision={2} style={{ width: '100%' }} placeholder="最低消费金额" />
            </Form.Item>
          </Space>
          <Form.Item name="total_count" label="发放总量" rules={[{ required: true, message: '请输入发放总量' }]}>
            <InputNumber min={1} precision={0} style={{ width: '100%' }} placeholder="请输入发放总量" />
          </Form.Item>
          <Form.Item name="valid_range" label="有效期" rules={[{ required: true, message: '请选择有效期' }]}>
            <DatePicker.RangePicker
              showTime
              style={{ width: '100%' }}
              placeholder={['生效时间', '失效时间']}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
