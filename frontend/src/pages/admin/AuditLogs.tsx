import { useState, useEffect } from 'react'
import { Card, Table, Typography, Tag, Select, Space, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import api from '@/services/api'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

interface AuditLog {
  id: number
  user_id: number
  action: string
  resource: string
  resource_id: number | null
  details: string | null
  ip_address: string | null
  created_at: string
}

interface FinanceAuditLog {
  id: number
  user_id: number
  audit_type: string
  amount: number | null
  description: string | null
  is_alert: boolean
  ip_address: string | null
  created_at: string
}

export default function AdminAuditLogs() {
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'operation' | 'finance'>('operation')
  const [operationLogs, setOperationLogs] = useState<AuditLog[]>([])
  const [financeLogs, setFinanceLogs] = useState<FinanceAuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [financeAlertFilter, setFinanceAlertFilter] = useState<string | undefined>()

  const fetchOperationLogs = async () => {
    try {
      setLoading(true)
      const res = await api.get('/audit/logs', { params: { page, page_size: pageSize } })
      setOperationLogs(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch (error) {
      console.error('获取操作日志失败', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchFinanceLogs = async () => {
    try {
      setLoading(true)
      const params: any = { page, page_size: pageSize }
      if (financeAlertFilter) {params.is_alert = financeAlertFilter}
      const res = await api.get('/audit/finance', { params })
      setFinanceLogs(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch (error) {
      console.error('获取财务审计日志失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'operation') {fetchOperationLogs()}
    else {fetchFinanceLogs()}
  }, [activeTab, page, financeAlertFilter])

  const operationColumns: ColumnsType<any> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户ID', dataIndex: 'user_id', width: 80 },
    { title: '操作', dataIndex: 'action', width: 120, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: '资源', dataIndex: 'resource', width: 100 },
    { title: '资源ID', dataIndex: 'resource_id', width: 80 },
    { title: '详情', dataIndex: 'details', ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', width: 120 },
    { title: '时间', dataIndex: 'created_at', width: 160, render: (v) => v ? new Date(v).toLocaleString() : '-' },
  ]

  const financeColumns: ColumnsType<any> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户ID', dataIndex: 'user_id', width: 80 },
    { title: '类型', dataIndex: 'audit_type', width: 120, render: (v) => <Tag color="green">{v}</Tag> },
    { title: '金额', dataIndex: 'amount', width: 100, render: (v) => v != null ? `¥${Number(v).toFixed(2)}` : '-' },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '告警', dataIndex: 'is_alert', width: 60, render: (v) => v ? <Tag color="red">是</Tag> : <Tag>否</Tag> },
    { title: 'IP', dataIndex: 'ip_address', width: 120 },
    { title: '时间', dataIndex: 'created_at', width: 160, render: (v) => v ? new Date(v).toLocaleString() : '-' },
  ]

  if (isMobile) {
    return (
      <div>
        <Card>
          <Title level={5}>审计日志</Title>
          <Space style={{ marginBottom: 12 }}>
            <Select value={activeTab} onChange={setActiveTab} size="small" style={{ width: 100 }}
              options={[{ label: '操作日志', value: 'operation' }, { label: '财务审计', value: 'finance' }]} />
            {activeTab === 'finance' && (
              <Select value={financeAlertFilter} onChange={setFinanceAlertFilter} size="small" style={{ width: 100 }}
                allowClear placeholder="告警筛选"
                options={[{ label: '仅告警', value: 'true' }, { label: '非告警', value: 'false' }]} />
            )}
          </Space>
          {loading ? <Spin /> : (
            activeTab === 'operation' ? (
              <ListView items={operationLogs} render={(item) => (
                <Card size="small" style={{ marginBottom: 8 }}>
                  <div><Tag color="blue">{item.action}</Tag> {item.resource}#{item.resource_id}</div>
                  <div style={{ fontSize: 12, color: '#999' }}>{item.ip_address} | {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}</div>
                </Card>
              )} />
            ) : (
              <ListView items={financeLogs} render={(item) => (
                <Card size="small" style={{ marginBottom: 8 }}>
                  <div><Tag color="green">{item.audit_type}</Tag> {item.is_alert && <Tag color="red">告警</Tag>}</div>
                  <div>金额: {item.amount != null ? `¥${item.amount.toFixed(2)}` : '-'}</div>
                  <div style={{ fontSize: 12, color: '#999' }}>{item.description}</div>
                </Card>
              )} />
            )
          )}
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>审计日志</Title>
          <Space>
            <Select value={activeTab} onChange={(v) => { setActiveTab(v); setPage(1) }} style={{ width: 120 }}
              options={[{ label: '操作日志', value: 'operation' }, { label: '财务审计', value: 'finance' }]} />
            {activeTab === 'finance' && (
              <Select value={financeAlertFilter} onChange={setFinanceAlertFilter} style={{ width: 120 }}
                allowClear placeholder="告警筛选"
                options={[{ label: '仅告警', value: 'true' }, { label: '非告警', value: 'false' }]} />
            )}
          </Space>
        </div>
      </Card>
      <Card style={{ marginTop: 16 }}>
        <Table
          columns={activeTab === 'operation' ? operationColumns : financeColumns}
          dataSource={activeTab === 'operation' ? operationLogs : financeLogs as any}
          rowKey="id"
          loading={loading}
          pagination={{ current: page, pageSize, total, onChange: setPage }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  )
}

function ListView<T>({ items, render }: { items: T[]; render: (item: T) => React.ReactNode }) {
  return <div>{items.map((item, i) => <div key={i}>{render(item)}</div>)}</div>
}
