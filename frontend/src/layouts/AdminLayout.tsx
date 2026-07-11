
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Space, Dropdown } from 'antd'
import { DashboardOutlined, LogoutOutlined, UserOutlined, ShopOutlined, TeamOutlined, InboxOutlined, AuditOutlined, SettingOutlined, TagOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'
import { useIsMobile } from '@/hooks/useIsMobile'
import api from '@/services/api'

const { Header, Content } = Layout

const tabItems = [
  { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '概览' },
  { key: '/admin/shops', icon: <ShopOutlined />, label: '店铺' },
  { key: '/admin/users', icon: <TeamOutlined />, label: '用户' },
  { key: '/admin/orders', icon: <InboxOutlined />, label: '订单' },
  { key: '/admin/coupons', icon: <TagOutlined />, label: '优惠券' },
  { key: '/admin/audit-logs', icon: <AuditOutlined />, label: '审计' },
  { key: '/admin/config', icon: <SettingOutlined />, label: '配置' },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { userInfo, logout } = useAuthStore()
  const isMobile = useIsMobile()

  const menuItems: MenuProps['items'] = [
    { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/admin/shops', icon: <ShopOutlined />, label: '店铺管理' },
    { key: '/admin/users', icon: <TeamOutlined />, label: '用户管理' },
    { key: '/admin/orders', icon: <InboxOutlined />, label: '订单管理' },
    { key: '/admin/coupons', icon: <TagOutlined />, label: '优惠券管理' },
    { key: '/admin/audit-logs', icon: <AuditOutlined />, label: '审计日志' },
    { key: '/admin/config', icon: <SettingOutlined />, label: '平台配置' },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
    },
    {
      type: 'divider',
    },
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
    } else if (key === 'profile') {
      navigate('/admin/profile')
    }
  }

  const getActiveKey = () => {
    const path = location.pathname
    const match = tabItems.find((item) => path.startsWith(item.key))
    return match ? match.key : '/admin/dashboard'
  }

  if (isMobile) {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <div className="mobile-header">
          <span className="header-title" style={{ color: '#f5222d' }}>🔧 管理后台</span>
          <div className="header-right">
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
              <Avatar icon={<UserOutlined />} size="small" style={{ backgroundColor: '#f5222d' }} />
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
              className={`bar-item ${getActiveKey() === item.key ? 'admin-active' : ''}`}
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
        <div style={{ marginRight: 48, fontSize: 20, fontWeight: 'bold', color: '#f5222d' }}>
          管理后台
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
