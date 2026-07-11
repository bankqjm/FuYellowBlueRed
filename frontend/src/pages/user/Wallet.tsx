import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, Form, Input, Radio, Button, message, List, Tag, Spin, Empty, Tabs } from 'antd'
import { WalletOutlined, WechatOutlined, BankOutlined, CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import api from '@/services/api'

const AMOUNT_OPTIONS = [10, 30, 50, 100, 200, 500]

interface RechargeRecord {
  trade_no: string
  amount: number | string
  channel: string
  status: string
  created_at?: string
}

interface TransactionRecord {
  id: number
  flow_type: string
  business_type: string
  amount: number | string
  description?: string
  created_at?: string
}

// 支付超时时间：15分钟（与后端order_timeout一致）
const PAYMENT_TIMEOUT_MS = 15 * 60 * 1000

const STATUS_MAP: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
  SUCCESS: { color: 'green', text: '成功', icon: <CheckCircleOutlined /> },
  PENDING: { color: 'orange', text: '待支付', icon: <ClockCircleOutlined /> },
  FAILED: { color: 'red', text: '失败', icon: <CloseCircleOutlined /> },
  TIMEOUT: { color: 'default', text: '超时', icon: <ExclamationCircleOutlined /> },
  CLOSED: { color: 'default', text: '已关闭', icon: <CloseCircleOutlined /> },
}

const FLOW_TYPE_MAP: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
  INCOME: { color: 'green', text: '收入', icon: <ArrowUpOutlined /> },
  EXPENSE: { color: 'red', text: '支出', icon: <ArrowDownOutlined /> },
  FREEZE: { color: 'orange', text: '冻结', icon: <ClockCircleOutlined /> },
  UNFREEZE: { color: 'blue', text: '解冻', icon: <CheckCircleOutlined /> },
}

const BUSINESS_TYPE_MAP: Record<string, string> = {
  ORDER_PAY: '订单支付',
  ORDER_REFUND: '订单退款',
  COMMISSION: '佣金',
  WITHDRAW: '提现',
  RECHARGE: '充值',
  BONUS: '奖励',
}

function formatCountdown(ms: number): string {
  if (ms <= 0) {return '00:00'}
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function channelLabel(ch: string) {
  switch (ch) {
    case 'WECHAT': return '微信支付'
    case 'UNIONPAY': return '银联云闪付'
    default: return ch
  }
}

export default function Wallet() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [currentTrade, setCurrentTrade] = useState<{ trade_no: string; amount: number; channel: string } | null>(null)
  const [records, setRecords] = useState<RechargeRecord[]>([])
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [balance, setBalance] = useState<number>(0)
  const [countdown, setCountdown] = useState<number>(0)
  const [tradeTimedOut, setTradeTimedOut] = useState(false)
  const [activeTab, setActiveTab] = useState('recharge')
  const [transactions, setTransactions] = useState<TransactionRecord[]>([])
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [transactionsTotal, setTransactionsTotal] = useState(0)
  const [transactionsPage, setTransactionsPage] = useState(1)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchBalance = useCallback(async () => {
    try {
      const res = await api.get('/wallet')
      setBalance(Number(res.data?.balance ?? 0))
    } catch {
      setBalance(0)
    }
  }, [])

  const fetchRecords = useCallback(async () => {
    try {
      setRecordsLoading(true)
      const res = await api.get('/payment/recharge/records')
      setRecords(res.data?.items || [])
    } catch {
      // error handled by interceptor
    } finally {
      setRecordsLoading(false)
    }
  }, [])

  const fetchTransactions = useCallback(async (page = 1) => {
    try {
      setTransactionsLoading(true)
      const res = await api.get('/wallet/transactions', { params: { page, page_size: 20 } })
      setTransactions(res.data?.items || [])
      setTransactionsTotal(res.data?.total || 0)
      setTransactionsPage(page)
    } catch {
      // error handled by interceptor
    } finally {
      setTransactionsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBalance()
    fetchRecords()
  }, [fetchBalance, fetchRecords])

  useEffect(() => {
    if (activeTab === 'transactions') {
      fetchTransactions(1)
    }
  }, [activeTab, fetchTransactions])

  // 支付超时倒计时
  useEffect(() => {
    if (currentTrade && !tradeTimedOut) {
      const startTime = Date.now()
      setCountdown(PAYMENT_TIMEOUT_MS)

      timerRef.current = setInterval(() => {
        const elapsed = Date.now() - startTime
        const remaining = PAYMENT_TIMEOUT_MS - elapsed

        if (remaining <= 0) {
          setCountdown(0)
          setTradeTimedOut(true)
          if (timerRef.current) {
            clearInterval(timerRef.current)
            timerRef.current = null
          }
          message.warning('支付超时，请重新发起充值')
        } else {
          setCountdown(remaining)
        }
      }, 1000)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [currentTrade, tradeTimedOut])

  const handleRecharge = async (values: any) => {
    try {
      setLoading(true)
      const res = await api.post('/payment/recharge', {
        amount: Number(values.amount),
        channel: values.channel,
      })
      if (res.data?.trade_no) {
        const status = res.data.status
        if (status === 'TIMEOUT') {
          message.error('支付超时，请稍后重试')
          fetchRecords()
          return
        }
        if (status === 'FAILED') {
          message.error('支付创建失败，请稍后重试')
          fetchRecords()
          return
        }
        setCurrentTrade({
          trade_no: res.data.trade_no,
          amount: Number(values.amount),
          channel: values.channel,
        })
        setTradeTimedOut(false)
        if (status === 'SUCCESS') {
          message.success('支付订单已创建')
        } else {
          message.info('订单待支付，请确认支付')
        }
      }
    } catch {
      // error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!currentTrade || tradeTimedOut) {return}
    try {
      setConfirming(true)
      await api.post('/payment/recharge/confirm', {
        trade_no: currentTrade.trade_no,
        channel: currentTrade.channel,
        status: 'SUCCESS',
      })
      message.success('充值成功！')
      setCurrentTrade(null)
      setTradeTimedOut(false)
      form.resetFields()
      fetchBalance()
      fetchRecords()
    } catch {
      setCurrentTrade(null)
      setTradeTimedOut(false)
      fetchRecords()
    } finally {
      setConfirming(false)
    }
  }

  const handleCancel = () => {
    setCurrentTrade(null)
    setTradeTimedOut(false)
    setCountdown(0)
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ textAlign: 'center' }}>
          <WalletOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
          <div style={{ fontSize: 14, color: '#8c8c8c' }}>账户余额</div>
          <div style={{ fontSize: 36, fontWeight: 700, color: '#1890ff', marginTop: 4 }}>
            ¥ {balance.toFixed(2)}
          </div>
        </div>
      </Card>

      <Card title="账户充值" style={{ marginBottom: 16 }}>
        {currentTrade ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
              充值金额：¥{currentTrade.amount.toFixed(2)}
            </div>
            <div style={{ color: '#8c8c8c', marginBottom: 4 }}>
              支付方式：{channelLabel(currentTrade.channel)}
            </div>
            <div style={{ color: '#8c8c8c', marginBottom: 16, fontSize: 12 }}>
              交易号：{currentTrade.trade_no}
            </div>
            {tradeTimedOut ? (
              <>
                <div style={{ background: '#fff2e8', border: '1px solid #ffbb96', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: 14, color: '#fa541c' }}>
                    支付已超时，请重新发起充值
                  </div>
                </div>
                <Button type="primary" onClick={handleCancel}>
                  返回重新充值
                </Button>
              </>
            ) : (
              <>
                <div style={{ background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: 14, color: '#52c41a' }}>
                    当前为模拟支付环境，点击下方按钮确认充值
                  </div>
                </div>
                <div style={{ fontSize: 14, color: countdown < 60000 ? '#ff4d4f' : '#8c8c8c', marginBottom: 16 }}>
                  支付剩余时间：{formatCountdown(countdown)}
                </div>
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                  <Button onClick={handleCancel}>取消</Button>
                  <Button type="primary" loading={confirming} onClick={handleConfirm}>
                    确认支付 ¥{currentTrade.amount.toFixed(2)}
                  </Button>
                </div>
              </>
            )}
          </div>
        ) : (
          <Form form={form} onFinish={handleRecharge} layout="vertical"
            initialValues={{ channel: 'WECHAT' }}
          >
            <Form.Item label="充值金额" name="amount" rules={[{ required: true, message: '请选择或输入充值金额' }]}>
              <Input type="number" prefix="¥" placeholder="请输入金额" size="large" min={1} max={10000} />
            </Form.Item>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 16 }}>
              {AMOUNT_OPTIONS.map((amt) => (
                <Button key={amt} onClick={() => form.setFieldsValue({ amount: amt })} style={{ height: 40 }}>
                  ¥{amt}
                </Button>
              ))}
            </div>
            <Form.Item label="支付方式" name="channel" rules={[{ required: true }]}>
              <Radio.Group>
                <Radio.Button value="WECHAT">
                  <WechatOutlined style={{ color: '#07c160' }} /> 微信支付
                </Radio.Button>
                <Radio.Button value="UNIONPAY">
                  <BankOutlined style={{ color: '#e21836' }} /> 银联云闪付
                </Radio.Button>
              </Radio.Group>
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block size="large">
                立即充值
              </Button>
            </Form.Item>
          </Form>
        )}
      </Card>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'recharge', label: '充值记录' },
            { key: 'transactions', label: '资金流水' },
          ]}
        />

        {activeTab === 'recharge' ? (
          recordsLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>
          ) : records.length === 0 ? (
            <Empty description="暂无充值记录" />
          ) : (
            <List
              dataSource={records}
              renderItem={(item: RechargeRecord) => {
                const statusInfo = STATUS_MAP[item.status] || STATUS_MAP.PENDING
                return (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 500 }}>充值 ¥{Number(item.amount).toFixed(2)}</div>
                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                          {channelLabel(item.channel)} · {item.trade_no?.slice(-8)}
                        </div>
                        <div style={{ fontSize: 12, color: '#bfbfbf' }}>{item.created_at}</div>
                      </div>
                      <Tag color={statusInfo.color} icon={statusInfo.icon}>{statusInfo.text}</Tag>
                    </div>
                  </List.Item>
                )
              }}
            />
          )
        ) : (
          transactionsLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>
          ) : transactions.length === 0 ? (
            <Empty description="暂无资金流水" />
          ) : (
            <List
              dataSource={transactions}
              pagination={transactionsTotal > 20 ? {
                current: transactionsPage,
                total: transactionsTotal,
                pageSize: 20,
                onChange: (page) => fetchTransactions(page),
                size: 'small',
              } : undefined}
              renderItem={(item: TransactionRecord) => {
                const flowInfo = FLOW_TYPE_MAP[item.flow_type] || FLOW_TYPE_MAP.EXPENSE
                const businessText = BUSINESS_TYPE_MAP[item.business_type] || item.business_type || ''
                const isIncome = item.flow_type === 'INCOME' || item.flow_type === 'UNFREEZE'
                return (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 500 }}>
                          {businessText} {isIncome ? '+' : '-'}¥{Number(item.amount).toFixed(2)}
                        </div>
                        {item.description && (
                          <div style={{ fontSize: 12, color: '#8c8c8c' }}>{item.description}</div>
                        )}
                        <div style={{ fontSize: 12, color: '#bfbfbf' }}>{item.created_at}</div>
                      </div>
                      <Tag color={flowInfo.color} icon={flowInfo.icon}>{flowInfo.text}</Tag>
                    </div>
                  </List.Item>
                )
              }}
            />
          )
        )}
      </Card>
    </div>
  )
}
