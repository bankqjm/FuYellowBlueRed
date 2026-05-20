
import { useState, useEffect, useCallback } from 'react'
import { Card, Typography, List, Spin, Empty, Tag, Space, Button, Modal, message, InputNumber, Pagination, Select } from 'antd'
import { WalletOutlined, HistoryOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import { walletApi, WalletInfo, TransactionInfo } from '../../services/wallet'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

const QUICK_AMOUNTS = [50, 100, 200, 500]

export default function Wallet() {
  const [loading, setLoading] = useState(true)
  const [wallet, setWallet] = useState<WalletInfo | null>(null)
  const [transactions, setTransactions] = useState<TransactionInfo[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [showRechargeModal, setShowRechargeModal] = useState(false)
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
  const [rechargeAmount, setRechargeAmount] = useState<number | null>(null)
  const [withdrawAmount, setWithdrawAmount] = useState<number | null>(null)
  const [withdrawMethod, setWithdrawMethod] = useState<string>('ALIPAY')
  const [withdrawAccount, setWithdrawAccount] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const isMobile = useIsMobile()
  const userInfo = useAuthStore((s) => s.userInfo)
  const isShopOwnerOrRider = userInfo?.role === 'SHOP_OWNER' || userInfo?.role === 'RIDER'

  const fetchWallet = async () => {
    try {
      const res = await walletApi.getWallet()
      setWallet(res.data)
    } catch (error) {
      console.error('获取钱包信息失败', error)
    }
  }

  const fetchTransactions = async () => {
    try {
      const res = await walletApi.getTransactions({ page, page_size: 20 })
      setTransactions(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      console.error('获取交易记录失败', error)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchWallet(), fetchTransactions()])
      setLoading(false)
    }
    loadData()
  }, [page])

  const handleRecharge = useCallback(async () => {
    if (!rechargeAmount || rechargeAmount <= 0) {
      message.warning('请输入有效的充值金额')
      return
    }
    setSubmitting(true)
    try {
      await walletApi.recharge(rechargeAmount)
      message.success('充值成功')
      setShowRechargeModal(false)
      setRechargeAmount(null)
      await Promise.all([fetchWallet(), fetchTransactions()])
    } catch (error: any) {
      const errMsg = error?.response?.data?.message || error?.message || '充值失败'
      message.error(errMsg)
    } finally {
      setSubmitting(false)
    }
  }, [rechargeAmount])

  const handleWithdraw = useCallback(async () => {
    if (!withdrawAmount || withdrawAmount <= 0) {
      message.warning('请输入有效的提现金额')
      return
    }
    if (!withdrawAccount.trim()) {
      message.warning('请输入收款账号')
      return
    }
    setSubmitting(true)
    try {
      await walletApi.withdraw(withdrawAmount, withdrawMethod, withdrawAccount)
      message.success('提现申请已提交')
      setShowWithdrawModal(false)
      setWithdrawAmount(null)
      setWithdrawAccount('')
      await Promise.all([fetchWallet(), fetchTransactions()])
    } catch (error: any) {
      const errMsg = error?.response?.data?.message || error?.message || '提现失败'
      message.error(errMsg)
    } finally {
      setSubmitting(false)
    }
  }, [withdrawAmount, withdrawMethod, withdrawAccount])

  const getTransactionTypeText = (type: string) => {
    const typeMap: Record<string, { text: string; color: string }> = {
      RECHARGE: { text: '充值', color: 'green' },
      PAYMENT: { text: '支付', color: 'blue' },
      ORDER_PAY: { text: '支付', color: 'blue' },
      REFUND: { text: '退款', color: 'orange' },
      ORDER_REFUND: { text: '退款', color: 'orange' },
      WITHDRAWAL: { text: '提现', color: 'red' },
      WITHDRAW: { text: '提现', color: 'red' },
      EARNING: { text: '收入', color: 'purple' },
      COMMISSION: { text: '平台抽成', color: 'cyan' },
      BONUS: { text: '奖金', color: 'purple' },
      PLATFORM_FEE: { text: '平台服务费', color: 'magenta' },
    }
    return typeMap[type] || { text: type, color: 'default' }
  }

  const isIncomeType = (flowType: string, businessType: string): boolean => {
    if (flowType === 'INCOME') return true
    const incomeBusinessTypes = ['RECHARGE', 'ORDER_REFUND', 'BONUS']
    return incomeBusinessTypes.includes(businessType)
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>我的钱包</Title>
          <Button
            type="text"
            icon={<QuestionCircleOutlined />}
            onClick={() => setShowInfoModal(true)}
          >
            说明
          </Button>
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <div style={{
          textAlign: 'center',
          padding: isMobile ? '20px 0' : '40px 0',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: 12,
          color: '#fff',
        }}>
          <div style={{ fontSize: 14, opacity: 0.9 }}>账户余额（元）</div>
          <div style={{ fontSize: isMobile ? 32 : 48, fontWeight: 700, marginTop: 8 }}>
            ¥{Number(wallet?.balance || 0).toFixed(2)}
          </div>
          {wallet && Number(wallet.frozen_balance) > 0 && (
            <div style={{ fontSize: 12, marginTop: 8, opacity: 0.8 }}>
              冻结金额：¥{Number(wallet.frozen_balance).toFixed(2)}
            </div>
          )}
        </div>

        {/* Recharge and Withdraw buttons (U-P2-03-FE) */}
        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', gap: 16 }}>
          <Button
            type="primary"
            size="large"
            style={{ minWidth: 120 }}
            onClick={() => setShowRechargeModal(true)}
          >
            充值
          </Button>
          {isShopOwnerOrRider && (
            <Button
              size="large"
              style={{ minWidth: 120 }}
              onClick={() => setShowWithdrawModal(true)}
            >
              提现
            </Button>
          )}
        </div>

        <div style={{ marginTop: 12, textAlign: 'center', color: '#999', fontSize: 12 }}>
          <WalletOutlined style={{ marginRight: 4 }} />
          余额可用于支付外卖订单
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <HistoryOutlined style={{ marginRight: 8 }} />
          <Text strong>交易记录</Text>
        </div>

        {transactions.length === 0 ? (
          <Empty description="暂无交易记录" />
        ) : (
          <>
            <List
              dataSource={transactions}
              renderItem={(item) => {
                const typeInfo = getTransactionTypeText(item.business_type || item.type)
                const isIncome = isIncomeType(item.flow_type, item.business_type || item.type)
                const amount = Number(item.amount)
                return (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Space>
                            <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
                            <Text>{item.description || typeInfo.text}</Text>
                          </Space>
                          <Text
                            strong
                            style={{
                              fontSize: 16,
                              color: isIncome ? '#52c41a' : '#ff4d4f',
                            }}
                          >
                            {isIncome ? '+' : '-'}{amount.toFixed(2)}
                          </Text>
                        </div>
                      }
                      description={
                        <div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                          </Text>
                          {item.balance_after !== undefined && item.balance_after !== null && (
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 12 }}>
                              余额: ¥{Number(item.balance_after).toFixed(2)}
                            </Text>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )
              }}
            />
            {/* Pagination (U-P2-03-FE) */}
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Pagination
                current={page}
                total={total}
                pageSize={20}
                onChange={(p) => setPage(p)}
                showSizeChanger={false}
                size={isMobile ? 'small' : 'default'}
              />
            </div>
          </>
        )}
      </Card>

      {/* Recharge Modal (U-P2-03-FE) */}
      <Modal
        title="充值申请"
        open={showRechargeModal}
        onCancel={() => {
          setShowRechargeModal(false)
          setRechargeAmount(null)
        }}
        onOk={handleRecharge}
        okText="提交申请"
        cancelText="取消"
        confirmLoading={submitting}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>充值金额：</Text>
          <InputNumber
            style={{ width: '100%', marginTop: 8 }}
            min={0.01}
            max={10000}
            precision={2}
            placeholder="请输入充值金额"
            value={rechargeAmount}
            onChange={(val) => setRechargeAmount(val)}
            addonAfter="元"
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text>快捷金额：</Text>
          <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {QUICK_AMOUNTS.map((amt) => (
              <Button
                key={amt}
                onClick={() => setRechargeAmount(amt)}
                type={rechargeAmount === amt ? 'primary' : 'default'}
              >
                ¥{amt}
              </Button>
            ))}
          </div>
        </div>
        <div style={{ padding: '8px 12px', background: '#fffbe6', borderRadius: 4, marginTop: 8 }}>
          <Text type="warning" style={{ fontSize: 12 }}>
            充值金额将立即到账，单笔最高10000元
          </Text>
        </div>
      </Modal>

      {/* Withdraw Modal (U-P2-03-FE, only for SHOP_OWNER/RIDER) */}
      <Modal
        title="申请提现"
        open={showWithdrawModal}
        onCancel={() => {
          setShowWithdrawModal(false)
          setWithdrawAmount(null)
          setWithdrawAccount('')
        }}
        onOk={handleWithdraw}
        okText="提交申请"
        cancelText="取消"
        confirmLoading={submitting}
      >
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">可提现余额：¥{Number(wallet?.balance || 0).toFixed(2)}</Text>
        </div>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">最低提现金额：¥10.00</Text>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text>提现金额：</Text>
          <InputNumber
            style={{ width: '100%', marginTop: 8 }}
            min={10}
            max={Number(wallet?.balance || 0)}
            precision={2}
            placeholder="请输入提现金额"
            value={withdrawAmount}
            onChange={(val) => setWithdrawAmount(val)}
            addonAfter="元"
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text>提现方式：</Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            value={withdrawMethod}
            onChange={setWithdrawMethod}
            options={[
              { label: '支付宝', value: 'ALIPAY' },
              { label: '微信', value: 'WECHAT' },
            ]}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text>收款账号：</Text>
          <InputNumber
            style={{ width: '100%', marginTop: 8 }}
            placeholder="请输入收款账号"
            value={withdrawAccount ? Number(withdrawAccount) : undefined}
            onChange={(val) => setWithdrawAccount(val ? String(val) : '')}
          />
        </div>
      </Modal>

      <Modal
        title="钱包说明"
        open={showInfoModal}
        onCancel={() => setShowInfoModal(false)}
        footer={null}
      >
        <div style={{ lineHeight: 1.8 }}>
          <p><strong>余额支付</strong></p>
          <p style={{ color: '#666' }}>下单时可以使用钱包余额支付，余额不足时需充值。</p>

          <p style={{ marginTop: 16 }}><strong>充值说明</strong></p>
          <p style={{ color: '#666' }}>点击充值按钮输入金额即可充值，充值金额将立即到账。</p>

          <p style={{ marginTop: 16 }}><strong>退款说明</strong></p>
          <p style={{ color: '#666' }}>订单取消后，已支付金额将原路退回至钱包余额。</p>

          <p style={{ marginTop: 16 }}><strong>提现说明</strong></p>
          <p style={{ color: '#666' }}>商家和骑手可在满足最低提现金额后申请提现。</p>
        </div>
      </Modal>
    </div>
  )
}
