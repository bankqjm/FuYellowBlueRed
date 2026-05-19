
import { useState, useEffect } from 'react'
import { Card, Typography, Table, Input, Select, Space, Button, Tag, message, Popconfirm } from 'antd'
import { SearchOutlined, StopOutlined, CheckOutlined } from '@ant-design/icons'
import api from '../../services/api'
import type { ColumnsType } from 'antd/es/table'
import { useIsMobile } from '@/hooks/useIsMobile'
import { getRoleInfo, ROLE_MAP } from '@/utils/role'

const { Title } = Typography

interface UserRecord {
  id: number
  phone: string
  nickname: string
  avatar?: string
  role: string
  status: number
  created_at?: string
}

export default function AdminUsers() {
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<UserRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [keyword, setKeyword] = useState('')
  const [role, setRole] = useState<string>('')
  const isMobile = useIsMobile()

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const params: Record<string, any> = { page, page_size: pageSize }
      if (keyword) {params.keyword = keyword}
      if (role) {params.role = role}
      const res = await api.get<{ items: UserRecord[]; total: number }>('/admin/users', { params })
      setUsers(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取用户列表失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [page, pageSize, keyword, role])

  const handleUpdateStatus = async (userId: number, newStatus: number) => {
    try {
      await api.put(`/admin/users/${userId}/status`, null, { params: { status: newStatus } })
      message.success('更新成功')
      fetchUsers()
    } catch (error) {
      console.error('更新状态失败', error)
    }
  }

  const columns: ColumnsType<UserRecord> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 130,
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      width: 120,
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 100,
      render: (roleStr: string) => {
        const info = getRoleInfo(roleStr)
        return <Tag color={info.color}>{info.text}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'red'}>
          {status === 1 ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      width: 180,
      render: (time: string) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.status === 1 ? (
            <Popconfirm
              title="确定禁用该用户？"
              onConfirm={() => handleUpdateStatus(record.id, 0)}
            >
              <Button size="small" danger icon={<StopOutlined />}>
                禁用
              </Button>
            </Popconfirm>
          ) : (
            <Popconfirm
              title="确定启用该用户？"
              onConfirm={() => handleUpdateStatus(record.id, 1)}
            >
              <Button size="small" type="primary" icon={<CheckOutlined />}>
                启用
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const renderMobileUsers = () => {
    if (users.length === 0) {
      return <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无用户数据</div>
    }
    return users.map((user) => {
      const roleInfo = getRoleInfo(user.role)
      return (
        <div className="mobile-card" key={user.id}>
          <div className="card-row">
            <span className="label">昵称</span>
            <span className="value">{user.nickname}</span>
          </div>
          <div className="card-row">
            <span className="label">手机号</span>
            <span className="value">{user.phone}</span>
          </div>
          <div className="card-row">
            <span className="label">角色</span>
            <span className="value"><Tag color={roleInfo.color}>{roleInfo.text}</Tag></span>
          </div>
          <div className="card-row">
            <span className="label">状态</span>
            <span className="value">
              <Tag color={user.status === 1 ? 'green' : 'red'}>
                {user.status === 1 ? '正常' : '禁用'}
              </Tag>
            </span>
          </div>
          {user.created_at && (
            <div className="card-row">
              <span className="label">注册时间</span>
              <span className="value" style={{ fontSize: 11 }}>{new Date(user.created_at).toLocaleString()}</span>
            </div>
          )}
          <div className="card-actions">
            {user.status === 1 ? (
              <Popconfirm title="确定禁用该用户？" onConfirm={() => handleUpdateStatus(user.id, 0)}>
                <Button size="small" danger icon={<StopOutlined />}>禁用</Button>
              </Popconfirm>
            ) : (
              <Popconfirm title="确定启用该用户？" onConfirm={() => handleUpdateStatus(user.id, 1)}>
                <Button size="small" type="primary" icon={<CheckOutlined />}>启用</Button>
              </Popconfirm>
            )}
          </div>
        </div>
      )
    })
  }

  return (
    <div>
      <Card>
        <Title level={4}>用户管理</Title>
      </Card>

      <Card style={{ marginTop: isMobile ? 8 : 16 }}>
        <Space style={{ marginBottom: 16, flexWrap: 'wrap' }} direction={isMobile ? 'vertical' : 'horizontal'}>
          <Input
            placeholder="搜索手机号/昵称"
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: isMobile ? '100%' : 200 }}
            allowClear
          />
          <Select
            placeholder="选择角色"
            value={role || undefined}
            onChange={(value) => setRole(value || '')}
            style={{ width: isMobile ? '100%' : 120 }}
            allowClear
          >
            {Object.entries(ROLE_MAP).map(([value, { text }]) => (
              <Select.Option key={value} value={value}>{text}</Select.Option>
            ))}
          </Select>
        </Space>

        {isMobile ? renderMobileUsers() : (
          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={loading}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (p, ps) => {
                setPage(p)
                setPageSize(ps || 20)
              },
            }}
          />
        )}
      </Card>
    </div>
  )
}
