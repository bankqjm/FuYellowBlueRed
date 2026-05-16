import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, Space, Select, message } from 'antd'
import { UserOutlined, LockOutlined, PhoneOutlined } from '@ant-design/icons'
import { authApi } from '@/services/auth'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title } = Typography

const roleOptions = [
  { label: '我是消费者', value: 'USER' },
  { label: '我是商家', value: 'SHOP_OWNER' },
  { label: '我是骑手', value: 'RIDER' },
]

export default function Register() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const isMobile = useIsMobile()

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
      localStorage.setItem('token', data.access_token)
      setAuth(data.access_token, {
        id: data.user_id,
        phone: '',
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
                { min: 6, message: '密码至少6位' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
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
