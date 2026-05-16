import { Card, Typography, List, Avatar, Space, Button, Tag, Divider } from 'antd'
import {
  UserOutlined,
  EditOutlined,
  EnvironmentOutlined,
  HeartOutlined,
  TagOutlined,
  CustomerServiceOutlined,
  SettingOutlined,
  RightOutlined,
  ShoppingOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { getRoleInfo } from '@/utils/role'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

export default function Profile() {
  const { userInfo, logout } = useAuthStore()
  const roleInfo = getRoleInfo(userInfo?.role)
  const navigate = useNavigate()
  const isMobile = useIsMobile()

  const menuItems = [
    { icon: <ShoppingOutlined />, label: '我的订单', action: () => navigate('/user/orders'), color: '#1890ff' },
    { icon: <EnvironmentOutlined />, label: '收货地址', action: () => navigate('/user/addresses'), color: '#52c41a' },
    { icon: <HeartOutlined />, label: '我的收藏', action: () => {}, color: '#eb2f96' },
    { icon: <TagOutlined />, label: '优惠券', action: () => {}, color: '#fa8c16' },
    { icon: <WalletOutlined />, label: '钱包', action: () => {}, color: '#722ed1' },
    { icon: <CustomerServiceOutlined />, label: '客服中心', action: () => {}, color: '#13c2c2' },
    { icon: <SettingOutlined />, label: '设置', action: () => {}, color: '#999' },
  ]

  if (isMobile) {
    return (
      <div>
        <div style={{
          background: 'linear-gradient(135deg, #1890ff, #0984e3)',
          padding: '24px 16px 20px',
          color: '#fff',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Avatar size={56} icon={<UserOutlined />} src={userInfo?.avatar} style={{ border: '2px solid rgba(255,255,255,0.5)' }} />
            <div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{userInfo?.nickname || '用户'}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                <Tag color={roleInfo.color} style={{ margin: 0, fontSize: 11 }}>{roleInfo.text}</Tag>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>{userInfo?.phone || ''}</Text>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', background: '#fff', padding: '12px 0', marginBottom: 8 }}>
          <div style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => navigate('/user/orders')}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>0</div>
            <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>待付款</div>
          </div>
          <div style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => navigate('/user/orders')}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#fa8c16' }}>0</div>
            <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>待收货</div>
          </div>
          <div style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => navigate('/user/orders')}>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>0</div>
            <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>待评价</div>
          </div>
        </div>

        <div style={{ background: '#fff' }}>
          {menuItems.map((item, index) => (
            <div
              key={item.label}
              onClick={item.action}
              style={{
                display: 'flex', alignItems: 'center', padding: '14px 16px',
                borderBottom: index < menuItems.length - 1 ? '1px solid #f5f5f5' : 'none',
                cursor: 'pointer', WebkitTapHighlightColor: 'transparent',
              }}
            >
              <span style={{ fontSize: 18, color: item.color, width: 28 }}>{item.icon}</span>
              <span style={{ flex: 1, fontSize: 14, marginLeft: 8 }}>{item.label}</span>
              <RightOutlined style={{ color: '#ccc', fontSize: 12 }} />
            </div>
          ))}
        </div>

        <div style={{ padding: '16px', marginTop: 8 }}>
          <Button danger block size="large" onClick={() => {
            logout()
            localStorage.removeItem('token')
            window.location.href = '/login'
          }}>
            退出登录
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space>
          <Avatar size={64} icon={<UserOutlined />} src={userInfo?.avatar} />
          <div>
            <Title level={4} style={{ margin: 0 }}>{userInfo?.nickname || '用户'}</Title>
            <Space style={{ marginTop: 4 }}>
              <Tag color={roleInfo.color}>{roleInfo.text}</Tag>
              <Text type="secondary">{userInfo?.phone || ''}</Text>
            </Space>
          </div>
        </Space>

        <Button icon={<EditOutlined />} block>编辑资料</Button>

        <Divider style={{ margin: '8px 0' }} />

        <List
          size="small"
          dataSource={menuItems}
          renderItem={(item) => (
            <List.Item style={{ cursor: 'pointer' }} onClick={item.action}>
              <Space>
                <span style={{ color: item.color }}>{item.icon}</span>
                <Text>{item.label}</Text>
              </Space>
              <RightOutlined style={{ color: '#ccc' }} />
            </List.Item>
          )}
        />

        <Button danger block onClick={() => {
          logout()
          localStorage.removeItem('token')
          window.location.href = '/login'
        }}>
          退出登录
        </Button>
      </Space>
    </Card>
  )
}
