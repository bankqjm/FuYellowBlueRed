import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, Space, Select, message, Progress } from 'antd'
import { UserOutlined, LockOutlined, PhoneOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { authApi } from '@/services/auth'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

const roleOptions = [
  { label: '我是消费者', value: 'USER' },
  { label: '我是商家', value: 'SHOP_OWNER' },
  { label: '我是骑手', value: 'RIDER' },
]

function getPasswordStrength(password: string): { score: number; label: string; color: string } {
  let score = 0
  if (password.length >= 8) score++
  if (/[a-z]/.test(password)) score++
  if (/[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++

  if (score <= 2) return { score: 20 * score, label: '弱', color: '#ff4d4f' }
  if (score <= 3) return { score: 20 * score, label: '中', color: '#faad14' }
  return { score: 20 * score, label: '强', color: '#52c41a' }
}

export default function Register() {
  const [loading, setLoading] = useState(false)
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const isMobile = useIsMobile()

  const strength = getPasswordStrength(password)

  const getHomePath = (role: string) => {
    switch (role) {
      case 'SHOP_OWNER':
        return '/shop'
      case 'RIDER':
        return '/rider'
      case 'ADMIN':
        return '/admin'
      default:
        return '/user/home'
    }
  }

  const onFinish = async (values: {
    phone: string
    password: string
    nickname: string
    role: string
  }) => {
    setLoading(true)
    try {
      await authApi.register(values)
      const res = await authApi.login({ phone: values.phone, password: values.password })
      const data = res.data
      setAuth({
        id: data.user_id,
        phone: values.phone,
        role: data.role,
        nickname: data.nickname,
        avatar: data.avatar,
        status: 1,
      })
      message.success('注册成功！')
      navigate(getHomePath(data.role))
    } catch (error) {
      console.error('注册失败', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: isMobile ? '16px' : 0,
    }}>
      <Card style={{
        width: isMobile ? '100%' : 400,
        maxWidth: 400,
        boxShadow: '0 14px 30px rgba(0,0,0,0.15)',
        borderRadius: isMobile ? 12 : 8,
      }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: 0 }}>
            🍜 FuYellowBlueRed
          </Title>
          <Title level={5} style={{ textAlign: 'center', marginBottom: 24, color: '#666' }}>
            创建您的账号
          </Title>
          <Form
            name="register"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="phone"
              rules={[
                { required: true, message: '请输入手机号' },
                { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' },
              ]}
            >
              <Input prefix={<PhoneOutlined />} placeholder="手机号" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少8位' },
                { pattern: /[a-z]/, message: '密码必须包含小写字母' },
                { pattern: /[A-Z]/, message: '密码必须包含大写字母' },
                { pattern: /\d/, message: '密码必须包含数字' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码（8位以上，含大小写字母和数字）" onChange={e => setPassword(e.target.value)} />
            </Form.Item>
            {password && (
              <div style={{ marginTop: -16, marginBottom: 16 }}>
                <Progress percent={strength.score} size="small" strokeColor={strength.color} format={() => strength.label} />
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  <span style={{ color: /[a-z]/.test(password) ? '#52c41a' : '#999' }}>
                    {/[a-z]/.test(password) ? <CheckCircleOutlined /> : <CloseCircleOutlined />} 小写字母
                  </span>
                  {' '}
                  <span style={{ color: /[A-Z]/.test(password) ? '#52c41a' : '#999' }}>
                    {/[A-Z]/.test(password) ? <CheckCircleOutlined /> : <CloseCircleOutlined />} 大写字母
                  </span>
                  {' '}
                  <span style={{ color: /\d/.test(password) ? '#52c41a' : '#999' }}>
                    {/\d/.test(password) ? <CheckCircleOutlined /> : <CloseCircleOutlined />} 数字
                  </span>
                  {' '}
                  <span style={{ color: password.length >= 8 ? '#52c41a' : '#999' }}>
                    {password.length >= 8 ? <CheckCircleOutlined /> : <CloseCircleOutlined />} 8位以上
                  </span>
                </div>
              </div>
            )}
            <Form.Item
              name="confirm_password"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
            </Form.Item>
            <Form.Item
              name="nickname"
              rules={[{ required: true, message: '请输入昵称' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="昵称" />
            </Form.Item>
            <Form.Item
              name="role"
              initialValue="USER"
              rules={[{ required: true, message: '请选择角色' }]}
            >
              <Select options={roleOptions} placeholder="选择您的身份" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                注册
              </Button>
            </Form.Item>
            <div style={{ textAlign: 'center' }}>
              已有账号？<Link to="/login">立即登录</Link>
            </div>
          </Form>
        </Space>
      </Card>
    </div>
  )
}
