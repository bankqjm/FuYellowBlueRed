import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography, Avatar, Dropdown, Space } from 'antd'
import {
  HomeOutlined,
  ShoppingCartOutlined,
  InboxOutlined,
  UserOutlined,
  EnvironmentOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'

const { Header, Content } = Layout
const { Text } = Typography

export default function UserLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { userInfo, logout } = useAuthStore()

  const menuItems: MenuProps['items'] = [
    { key: '/user/home', icon: <HomeOutlined />, label: '首页' },
    { key: '/user/cart', icon: <ShoppingCartOutlined />, label: '购物车' },
    { key: '/user/orders', icon: <InboxOutlined />, label: '我的订单' },
    { key: '/user/addresses', icon: <EnvironmentOutlined />, label: '收货地址' },
    { key: '/user/profile', icon: <UserOutlined />, label: '个人中心' },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key)
  }

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      localStorage.removeItem('token')
      navigate('/login')
    }
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
        <div style={{ marginRight: 48, fontSize: 20, fontWeight: 'bold', color: '#1890ff' }}>
          🍜 FuYellowBlueRed
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ flex: 1, border: 'none' }}
        />
        <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} src={userInfo?.avatar} />
            <Text>{userInfo?.nickname || '用户'}</Text>
          </Space>
        </Dropdown>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
