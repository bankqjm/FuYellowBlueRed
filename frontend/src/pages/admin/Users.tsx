
import { useState, useEffect } from 'react'
import { Card, Typography, Table, Input, Select, Space, Button, Tag, message, Popconfirm } from 'antd'
import { SearchOutlined, StopOutlined, CheckOutlined } from '@ant-design/icons'
import api from '../../services/api'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

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

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const params: Record<string, any> = { page, page_size: pageSize }
      if (keyword) params.keyword = keyword
      if (role) params.role = role
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

  const getRoleTag = (role: string) => {
    const map: Record<string, { text: string; color: string }> = {
      USER: { text: '普通用户', color: 'blue' },
      SHOP_OWNER: { text: '商家', color: 'green' },
      RIDER: { text: '骑手', color: 'orange' },
      ADMIN: { text: '管理员', color: 'red' },
    }
    return map[role] || { text: role, color: 'default' }
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
      render: (role: string) => {
        const tag = getRoleTag(role)
        return <Tag color={tag.color}>{tag.text}</Tag>
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

  return (
    <div>
      <Card>
        <Title level={4}>用户管理</Title>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索手机号/昵称"
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="选择角色"
            value={role || undefined}
            onChange={(value) => setRole(value || '')}
            style={{ width: 120 }}
            allowClear
          >
            <Select.Option value="USER">普通用户</Select.Option>
            <Select.Option value="SHOP_OWNER">商家</Select.Option>
            <Select.Option value="RIDER">骑手</Select.Option>
            <Select.Option value="ADMIN">管理员</Select.Option>
          </Select>
        </Space>

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
      </Card>
    </div>
  )
}

