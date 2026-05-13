
import { Outlet, useNavigate } from 'react-router-dom'
import { Layout, Menu, Avatar, Space, Dropdown } from 'antd'
import { InboxOutlined, LogoutOutlined, WalletOutlined, DollarOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'

const { Header, Content } = Layout

export default function RiderLayout() {
  const navigate = useNavigate()
  const { userInfo, logout } = useAuthStore()

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

