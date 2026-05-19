
import { useState } from 'react'
import { Card, Typography, List, Collapse, Input, Button, message, Space, Tag } from 'antd'
import {
  CustomerServiceOutlined,
  PhoneOutlined,
  MailOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Panel } = Collapse

const faqItems = [
  {
    question: '如何下单？',
    answer: '选择您喜欢的商家和商品，点击"加入购物车"，确认商品后点击"去结算"，填写收货地址，选择支付方式后即可下单。',
  },
  {
    question: '如何取消订单？',
    answer: '在"我的订单"页面，找到待支付或待接单的订单，点击"取消订单"即可。已接单或配送中的订单无法取消。',
  },
  {
    question: '订单超时未支付会自动取消吗？',
    answer: '是的，订单下单后有15分钟的支付时间，超时未支付订单将自动取消。',
  },
  {
    question: '如何联系骑手？',
    answer: '在骑手端订单详情页面，点击"拨打电话"按钮即可联系骑手。',
  },
  {
    question: '退款多久到账？',
    answer: '订单取消或退款后，退款金额将原路返回至您的钱包余额，通常即时到账。',
  },
  {
    question: '商家拒单后怎么办？',
    answer: '商家拒单后订单将自动取消，已支付金额会原路退回。如需继续下单，可重新选择商家。',
  },
  {
    question: '如何成为骑手？',
    answer: '请联系平台管理员申请开通骑手权限，通过审核后即可开始接单配送。',
  },
  {
    question: '配送费如何计算？',
    answer: '配送费由商家设置，根据距离和时段有所不同。具体费用以下单页面显示为准。',
  },
]

export default function Support() {
  const [feedback, setFeedback] = useState('')
  const [contact, setContact] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const isMobile = useIsMobile()

  const handleSubmit = async () => {
    if (!feedback.trim()) {
      message.warning('请输入您的反馈内容')
      return
    }
    setSubmitting(true)
    setTimeout(() => {
      message.success('反馈已提交，我们会尽快处理')
      setFeedback('')
      setContact('')
      setSubmitting(false)
    }, 1000)
  }

  return (
    <div>
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <CustomerServiceOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={4} style={{ margin: 0 }}>客服中心</Title>
          <Text type="secondary">有任何问题，请随时联系我们</Text>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
          gap: 16,
          marginBottom: 24,
        }}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <PhoneOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
            <div style={{ fontWeight: 600 }}>电话客服</div>
            <Text type="secondary">400-888-8888</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>工作日 9:00-18:00</Text>
          </Card>

          <Card size="small" style={{ textAlign: 'center' }}>
            <MailOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
            <div style={{ fontWeight: 600 }}>邮箱反馈</div>
            <Text type="secondary">support@fuyellowbluered.com</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>24小时内回复</Text>
          </Card>

          <Card size="small" style={{ textAlign: 'center' }}>
            <MessageOutlined style={{ fontSize: 24, color: '#722ed1', marginBottom: 8 }} />
            <div style={{ fontWeight: 600 }}>在线客服</div>
            <Text type="secondary">微信公众号</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>搜索"FuYellowBlueRed"</Text>
          </Card>
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Title level={5}>
          <QuestionCircleOutlined style={{ marginRight: 8 }} />
          常见问题
        </Title>
        <Collapse defaultActiveKey={['0']} ghost>
          {faqItems.map((item, index) => (
            <Panel header={item.question} key={index}>
              <Paragraph style={{ margin: 0, color: '#666' }}>{item.answer}</Paragraph>
            </Panel>
          ))}
        </Collapse>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Title level={5}>
          <MessageOutlined style={{ marginRight: 8 }} />
          意见反馈
        </Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text type="secondary" style={{ marginBottom: 8, display: 'block' }}>反馈内容（必填）</Text>
            <TextArea
              rows={4}
              placeholder="请详细描述您的问题或建议..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              maxLength={500}
              showCount
            />
          </div>
          <div>
            <Text type="secondary" style={{ marginBottom: 8, display: 'block' }}>联系方式（选填）</Text>
            <Input
              placeholder="手机号或邮箱，方便我们联系您"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              maxLength={50}
            />
          </div>
          <Button
            type="primary"
            block
            size="large"
            loading={submitting}
            onClick={handleSubmit}
          >
            提交反馈
          </Button>
        </Space>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <div style={{ textAlign: 'center' }}>
          <Space>
            <Tag icon={<ClockCircleOutlined />} color="default">服务时间</Tag>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">周一至周日 08:00 - 22:00</Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              法定节假日服务时间可能调整，请关注公告
            </Text>
          </div>
        </div>
      </Card>
    </div>
  )
}
