import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Space, Dropdown } from 'antd'
import { InboxOutlined, LogoutOutlined, ShopOutlined, ShoppingOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Header, Content } = Layout

const tabItems = [
  { key: '/shop/info', icon: <ShopOutlined />, label: '店铺' },
  { key: '/shop/products', icon: <ShoppingOutlined />, label: '商品' },
  { key: '/shop/orders', icon: <InboxOutlined />, label: '订单' },
]

export default function ShopLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { userInfo, logout } = useAuthStore()
  const isMobile = useIsMobile()

  const menuItems: MenuProps['items'] = [
    { key: '/shop/info', icon: <ShopOutlined />, label: '店铺信息' },
    { key: '/shop/products', icon: <ShoppingOutlined />, label: '商品管理' },
    { key: '/shop/orders', icon: <InboxOutlined />, label: '订单管理' },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      localStorage.removeItem('token')
      navigate('/login')
    }
  }

  const getActiveKey = () => {
    const path = location.pathname
    const match = tabItems.find(item => path.startsWith(item.key))
    return match ? match.key : '/shop/info'
  }

  if (isMobile) {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <div className="mobile-header">
          <span className="header-title" style={{ color: '#fa8c16' }}>🏪 商家管理</span>
          <div className="header-right">
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
              <Avatar icon={<ShopOutlined />} size="small" style={{ backgroundColor: '#fa8c16' }} />
            </Dropdown>
          </div>
        </div>
        <div className="mobile-content">
          <Outlet />
        </div>
        <div className="mobile-bottom-bar">
          {tabItems.map(item => (
            <div
              key={item.key}
              className={`bar-item ${getActiveKey() === item.key ? 'shop-active' : ''}`}
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
        <div style={{ marginRight: 48, fontSize: 20, fontWeight: 'bold', color: '#fa8c16' }}>
          🏪 商家管理后台
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
            <Avatar icon={<ShopOutlined />} />
            <span>{userInfo?.nickname || '商家'}</span>
          </Space>
        </Dropdown>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
