
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Space, Dropdown } from 'antd'
import { InboxOutlined, LogoutOutlined, WalletOutlined, DollarOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'
import api from '@/services/api'

const { Header, Content } = Layout

const tabItems = [
  { key: '/rider/orders', icon: <InboxOutlined />, label: '接单' },
  { key: '/rider/earnings', icon: <WalletOutlined />, label: '收入' },
  { key: '/rider/withdraw', icon: <DollarOutlined />, label: '提现' },
]

export default function RiderLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { userInfo, logout } = useAuthStore()
  const isMobile = useIsMobile()

  const menuItems: MenuProps['items'] = [
    { key: '/rider/orders', icon: <InboxOutlined />, label: '订单管理' },
    { key: '/rider/earnings', icon: <WalletOutlined />, label: '我的收入' },
    { key: '/rider/withdraw', icon: <DollarOutlined />, label: '提现' },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleUserMenuClick: MenuProps['onClick'] = async ({ key }) => {
    if (key === 'logout') {
      try { await api.post('/auth/logout') } catch {}
      logout()
      navigate('/login')
    }
  }

  const getActiveKey = () => {
    const path = location.pathname
    const match = tabItems.find((item) => path.startsWith(item.key))
    return match ? match.key : '/rider/orders'
  }

  if (isMobile) {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <div className="mobile-header">
          <span className="header-title" style={{ color: '#52c41a' }}>🛵 骑手配送</span>
          <div className="header-right">
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
              <Avatar size="small" style={{ backgroundColor: '#52c41a' }}>骑</Avatar>
            </Dropdown>
          </div>
        </div>
        <div className="mobile-content">
          <Outlet />
        </div>
        <div className="mobile-bottom-bar">
          {tabItems.map((item) => (
            <div
              key={item.key}
              className={`bar-item ${getActiveKey() === item.key ? 'rider-active' : ''}`}
              onClick={() => navigate(item.key)}
            >
              <span className="bar-icon">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: '#fff',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}>
        <div style={{ marginRight: 48, fontSize: 20, fontWeight: 'bold', color: '#52c41a' }}>
          骑手配送
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, border: 'none' }}
        />
        <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
          <Space style={{ cursor: 'pointer' }}>
            <Avatar style={{ backgroundColor: '#52c41a' }}>骑</Avatar>
            <span>{userInfo?.nickname || '骑手'}</span>
          </Space>
        </Dropdown>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
