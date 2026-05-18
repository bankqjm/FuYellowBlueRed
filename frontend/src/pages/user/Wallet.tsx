
import { useState, useEffect } from 'react'
import { Card, Typography, List, Spin, Empty, Tag, Space, Button, Modal, message } from 'antd'
import { WalletOutlined, HistoryOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import { walletApi, WalletInfo, TransactionInfo } from '../../services/wallet'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

export default function Wallet() {
  const [loading, setLoading] = useState(true)
  const [wallet, setWallet] = useState<WalletInfo | null>(null)
  const [transactions, setTransactions] = useState<TransactionInfo[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const isMobile = useIsMobile()

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

  const getTransactionTypeText = (type: string) => {
    const typeMap: Record<string, { text: string; color: string }> = {
      RECHARGE: { text: '充值', color: 'green' },
      PAYMENT: { text: '支付', color: 'blue' },
      REFUND: { text: '退款', color: 'orange' },
      WITHDRAWAL: { text: '提现', color: 'red' },
      EARNING: { text: '收入', color: 'purple' },
      COMMISSION: { text: '平台抽成', color: 'cyan' },
      PLATFORM_FEE: { text: '平台服务费', color: 'magenta' },
    }
    return typeMap[type] || { text: type, color: 'default' }
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
            ¥{(wallet?.balance || 0).toFixed(2)}
          </div>
          {wallet && wallet.frozen_balance > 0 && (
            <div style={{ fontSize: 12, marginTop: 8, opacity: 0.8 }}>
              冻结金额：¥{wallet.frozen_balance.toFixed(2)}
            </div>
          )}
        </div>

        <div style={{ marginTop: 16, textAlign: 'center', color: '#999', fontSize: 12 }}>
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
          <List
            dataSource={transactions}
            renderItem={(item) => {
              const typeInfo = getTransactionTypeText(item.type)
              const isIncome = ['RECHARGE', 'REFUND', 'EARNING'].includes(item.type)
              return (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
                        <Text type={isIncome ? 'success' : undefined}>
                          {isIncome ? '+' : '-'}{Math.abs(item.amount).toFixed(2)}
                        </Text>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.description || typeInfo.text}
                        </Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )
            }}
          />
        )}
      </Card>

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
          <p style={{ color: '#666' }}>钱包充值由平台管理员操作，如有充值需求请联系客服。</p>

          <p style={{ marginTop: 16 }}><strong>退款说明</strong></p>
          <p style={{ color: '#666' }}>订单取消后，已支付金额将原路退回至钱包余额。</p>

          <p style={{ marginTop: 16 }}><strong>提现说明</strong></p>
          <p style={{ color: '#666' }}>商家和骑手可在满足最低提现金额后申请提现。</p>
        </div>
      </Modal>
    </div>
  )
}
