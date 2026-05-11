import { Outlet, useNavigate } from 'react-router-dom'
import { Layout, Menu, Typography, Avatar, Space, Dropdown } from 'antd'
import { DashboardOutlined, LogoutOutlined, UserOutlined, ShopOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'

const { Header, Content } = Layout

export default function AdminLayout() {
  const navigate = useNavigate()
  const { userInfo, logout } = useAuthStore()

  const menuItems: MenuProps['items'] = [
    { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/admin/shops', icon: <ShopOutlined />, label: '店铺审核' },
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
        <div style={{ marginRight: 48, fontSize: 20, fontWeight: 'bold', color: '#f5222d' }}>
          ⚙️ 管理后台
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
            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#f5222d' }} />
            <span>{userInfo?.nickname || '管理员'}</span>
          </Space>
        </Dropdown>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
