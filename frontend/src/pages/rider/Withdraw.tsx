
import { useState, useEffect } from 'react'
import { Card, Typography, Statistic, Row, Col, List, Empty, Spin, Button, InputNumber, message, Form } from 'antd'
import { WalletOutlined, DollarOutlined } from '@ant-design/icons'
import { riderApi, EarningsSummary, WithdrawalRecord } from '../../services/rider'

const { Title, Text } = Typography

export default function RiderWithdraw() {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<EarningsSummary | null>(null)
  const [records, setRecords] = useState<WithdrawalRecord[]>([])
  const [withdrawAmount, setWithdrawAmount] = useState<number>(0)
  const [form] = Form.useForm()

  const fetchSummary = async () => {
    try {
      const res = await riderApi.getEarningsSummary()
      setSummary(res.data)
    } catch (error) {
      console.error('获取余额失败', error)
    }
  }

  const fetchRecords = async () => {
    try {
      setLoading(true)
      const res = await riderApi.getWithdrawalRecords()
      setRecords(res.data.items)
    } catch (error) {
      console.error('获取提现记录失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
    fetchRecords()
  }, [])

  const handleWithdraw = async () => {
    if (withdrawAmount <= 0) {
      message.error('请输入正确的提现金额')
      return
    }
    if (withdrawAmount > (summary?.balance || 0)) {
      message.error('余额不足')
      return
    }

    try {
      setLoading(true)
      await riderApi.withdraw(withdrawAmount)
      message.success('提现成功')
      setWithdrawAmount(0)
      fetchSummary()
      fetchRecords()
    } catch (error) {
      console.error('提现失败', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusText = (status: string) => {
    const map: Record<string, { text: string; color: string }> = {
      PENDING: { text: '处理中', color: 'orange' },
      COMPLETED: { text: '已完成', color: 'green' },
      REJECTED: { text: '已拒绝', color: 'red' },
    }
    return map[status] || { text: status, color: 'default' }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Card>
        <Title level={4}>提现</Title>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card>
            <Statistic
              title="可提现余额"
              value={summary?.balance || 0}
              prefix={<WalletOutlined />}
              precision={2}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 16 }}>
        <Title level={5}>提现</Title>
        <Form form={form} layout="vertical">
          <Form.Item label="提现金额">
            <InputNumber
              style={{ width: '100%' }}
              min={0.01}
              max={summary?.balance || 0}
              precision={2}
              value={withdrawAmount}
              onChange={(value) => setWithdrawAmount(value || 0)}
              addonAfter="元"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              size="large"
              icon={<DollarOutlined />}
              onClick={handleWithdraw}
              loading={loading}
              style={{ width: '100%' }}
            >
              提现
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Title level={5}>提现记录</Title>
        {records.length === 0 ? (
          <Empty description="暂无提现记录" style={{ marginTop: 50 }} />
        ) : (
          <List
            dataSource={records}
            renderItem={(item) => {
              const statusInfo = getStatusText(item.status)
              return (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Text>
                        ¥{item.amount.toFixed(2)} - {item.method}
                      </Text>
                    }
                    description={item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                  />
                  <Text style={{ color: statusInfo.color }}>{statusInfo.text}</Text>
                </List.Item>
              )
            }}
          />
        )}
      </Card>
    </div>
  )
}

