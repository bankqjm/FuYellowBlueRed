import { Card, Typography, Avatar, Button, Tag, Divider, Switch, Modal, Form, Input, Upload, message } from 'antd'
import {
  UserOutlined,
  EditOutlined,
  EnvironmentOutlined,
  HeartOutlined,
  TagOutlined,
  CustomerServiceOutlined,
  RightOutlined,
  ShoppingOutlined,
  WalletOutlined,
  MoonOutlined,
  SunOutlined,
  LockOutlined,
  CameraOutlined,
  ShopOutlined,
  CarOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { getRoleInfo } from '@/utils/role'
import { useIsMobile } from '@/hooks/useIsMobile'
import { useTheme } from '@/contexts/ThemeContext'
import api from '@/services/api'
import { uploadApi } from '@/services/upload'
import { useState, useMemo } from 'react'

const { Text } = Typography

interface MenuItem {
  icon: React.ReactNode
  label: string
  action: () => void
  color: string
  isSwitch?: boolean
  isDark?: boolean
}

export default function Profile() {
  const { userInfo, logout, updateUserInfo } = useAuthStore()
  const roleInfo = getRoleInfo(userInfo?.role)
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = useIsMobile()
  const { theme, toggleTheme } = useTheme()
  const [avatarModalVisible, setAvatarModalVisible] = useState(false)
  const [passwordModalVisible, setPasswordModalVisible] = useState(false)
  const [nicknameModalVisible, setNicknameModalVisible] = useState(false)
  const [avatarUrl, setAvatarUrl] = useState<string>(userInfo?.avatar || '')
  const [nicknameForm] = Form.useForm()
  const [passwordForm] = Form.useForm()

  const role = userInfo?.role || 'USER'

  // 根据当前路径前缀判断返回路径
  const basePath = useMemo(() => {
    const path = location.pathname
    if (path.startsWith('/shop')) {return '/shop'}
    if (path.startsWith('/rider')) {return '/rider'}
    if (path.startsWith('/admin')) {return '/admin'}
    return '/user'
  }, [location.pathname])

  // 根据角色生成不同的菜单项
  const menuItems: MenuItem[] = useMemo(() => {
    const common: MenuItem[] = [
      { icon: <LockOutlined />, label: '修改密码', action: () => setPasswordModalVisible(true), color: '#fa541c' },
      { icon: theme === 'dark' ? <SunOutlined /> : <MoonOutlined />, label: '暗色模式', action: () => toggleTheme(), color: '#666', isSwitch: true, isDark: theme === 'dark' },
    ]

    if (role === 'USER') {
      return [
        { icon: <ShoppingOutlined />, label: '我的订单', action: () => navigate('/user/orders'), color: '#1890ff' },
        { icon: <EnvironmentOutlined />, label: '收货地址', action: () => navigate('/user/addresses'), color: '#52c41a' },
        { icon: <HeartOutlined />, label: '我的收藏', action: () => navigate('/user/favorites'), color: '#eb2f96' },
        { icon: <TagOutlined />, label: '优惠券', action: () => navigate('/user/coupons'), color: '#fa8c16' },
        { icon: <WalletOutlined />, label: '钱包', action: () => navigate('/user/wallet'), color: '#722ed1' },
        { icon: <CustomerServiceOutlined />, label: '客服中心', action: () => navigate('/user/support'), color: '#13c2c2' },
        ...common,
      ]
    }

    if (role === 'SHOP_OWNER') {
      return [
        { icon: <ShopOutlined />, label: '店铺管理', action: () => navigate('/shop/info'), color: '#1890ff' },
        { icon: <ShoppingOutlined />, label: '商品管理', action: () => navigate('/shop/products'), color: '#52c41a' },
        { icon: <WalletOutlined />, label: '收益管理', action: () => navigate('/shop/earnings'), color: '#722ed1' },
        ...common,
      ]
    }

    if (role === 'RIDER') {
      return [
        { icon: <CarOutlined />, label: '接单中心', action: () => navigate('/rider/orders'), color: '#52c41a' },
        { icon: <WalletOutlined />, label: '我的收入', action: () => navigate('/rider/earnings'), color: '#722ed1' },
        ...common,
      ]
    }

    if (role === 'ADMIN') {
      return [
        { icon: <DashboardOutlined />, label: '管理后台', action: () => navigate('/admin/dashboard'), color: '#1890ff' },
        ...common,
      ]
    }

    return common
  }, [role, theme, basePath, navigate, toggleTheme])

  const handleAvatarUpload = async (file: File) => {
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件')
      return false
    }
    const isLt5M = file.size / 1024 / 1024 < 5
    if (!isLt5M) {
      message.error('图片大小不能超过 5MB')
      return false
    }
    try {
      const res = await uploadApi.upload(file)
      setAvatarUrl(res.data.url)
      await api.put('/users/me', { avatar: res.data.url })
      updateUserInfo({ avatar: res.data.url })
      message.success('头像更新成功')
      setAvatarModalVisible(false)
    } catch {
      message.error('头像上传失败')
    }
    return false
  }

  const handleNicknameUpdate = async (values: any) => {
    try {
      await api.put('/users/me', { nickname: values.nickname })
      updateUserInfo({ nickname: values.nickname })
      message.success('昵称修改成功')
      setNicknameModalVisible(false)
    } catch {
      message.error('昵称修改失败')
    }
  }

  const handleChangePassword = async (values: any) => {
    try {
      await api.post('/auth/change-password', {
        old_password: values.old_password,
        new_password: values.new_password,
      })
      message.success('密码修改成功，请重新登录')
      setPasswordModalVisible(false)
      passwordForm.resetFields()
      try { await api.post('/auth/logout') } catch {}
      logout()
      window.location.href = '/login'
    } catch {
      // error handled by interceptor
    }
  }

  const handleLogout = async () => {
    try { await api.post('/auth/logout') } catch {}
    logout()
    window.location.href = '/login'
  }

  // 用户信息头部区域
  const renderUserInfo = () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ position: 'relative' }}>
        <Avatar size={isMobile ? 56 : 64} icon={<UserOutlined />} src={userInfo?.avatar}
          style={{ border: '2px solid #f0f0f0' }}
        />
        <div
          onClick={() => setAvatarModalVisible(true)}
          style={{
            position: 'absolute', bottom: -2, right: -2,
            width: isMobile ? 20 : 22, height: isMobile ? 20 : 22, borderRadius: '50%',
            background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
          }}
        >
          <CameraOutlined style={{ fontSize: isMobile ? 11 : 12, color: '#1890ff' }} />
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: isMobile ? 18 : 20, fontWeight: 700 }}>{userInfo?.nickname || '用户'}</span>
          <EditOutlined style={{ fontSize: 14, cursor: 'pointer', color: '#1890ff' }} onClick={() => {
            nicknameForm.setFieldsValue({ nickname: userInfo?.nickname || '' })
            setNicknameModalVisible(true)
          }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
          <Tag color={roleInfo.color} style={{ margin: 0 }}>{roleInfo.text}</Tag>
          <Text type="secondary" style={{ fontSize: 13 }}>{userInfo?.phone || ''}</Text>
        </div>
      </div>
    </div>
  )

  // 菜单列表区域
  const renderMenuList = () => (
    <div>
      {menuItems.map((item, index) => (
        <div
          key={item.label}
          onClick={() => !item.isSwitch && item.action()}
          style={{
            display: 'flex', alignItems: 'center', padding: isMobile ? '14px 16px' : '12px 4px',
            borderBottom: index < menuItems.length - 1 ? '1px solid #f5f5f5' : 'none',
            cursor: item.isSwitch ? 'default' : 'pointer',
            WebkitTapHighlightColor: 'transparent',
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => !item.isSwitch && (e.currentTarget.style.background = '#fafafa')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <span style={{ fontSize: 18, color: item.color, width: 28, textAlign: 'center' }}>{item.icon}</span>
          <span style={{ flex: 1, fontSize: 14, marginLeft: 12 }}>{item.label}</span>
          {item.isSwitch ? (
            <Switch checked={item.isDark} onChange={() => toggleTheme()} size="small" />
          ) : (
            <RightOutlined style={{ color: '#ccc', fontSize: 12 }} />
          )}
        </div>
      ))}
    </div>
  )

  // 模态框们
  const renderModals = () => (
    <>
      <Modal title="更换头像" open={avatarModalVisible} onCancel={() => setAvatarModalVisible(false)} footer={null}>
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Avatar size={80} icon={<UserOutlined />} src={avatarUrl || userInfo?.avatar} style={{ marginBottom: 16 }} />
          <div>
            <Upload accept="image/*" showUploadList={false} beforeUpload={handleAvatarUpload}>
              <Button type="primary" icon={<CameraOutlined />}>选择图片上传</Button>
            </Upload>
          </div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>支持 jpg/png，不超过5MB</div>
        </div>
      </Modal>

      <Modal title="修改昵称" open={nicknameModalVisible} onCancel={() => setNicknameModalVisible(false)} onOk={() => nicknameForm.submit()}>
        <Form form={nicknameForm} onFinish={handleNicknameUpdate} layout="vertical">
          <Form.Item name="nickname" label="昵称" rules={[{ required: true, message: '请输入昵称' }]}>
            <Input placeholder="请输入新昵称" maxLength={50} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="修改密码" open={passwordModalVisible} onCancel={() => { setPasswordModalVisible(false); passwordForm.resetFields() }} onOk={() => passwordForm.submit()}>
        <Form form={passwordForm} onFinish={handleChangePassword} layout="vertical">
          <Form.Item name="old_password" label="原密码" rules={[{ required: true, message: '请输入原密码' }]}>
            <Input.Password placeholder="请输入原密码" />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[
            { required: true, message: '请输入新密码' },
            { min: 8, message: '密码至少8位' },
            { pattern: /[a-z]/, message: '需包含小写字母' },
            { pattern: /[A-Z]/, message: '需包含大写字母' },
            { pattern: /\d/, message: '需包含数字' },
          ]}>
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认新密码" dependencies={['new_password']} rules={[
            { required: true, message: '请确认新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error('两次输入的密码不一致'))
              },
            }),
          ]}>
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )

  if (isMobile) {
    return (
      <div style={{ background: '#f5f5f5', minHeight: '100vh' }}>
        <div style={{
          background: 'linear-gradient(135deg, #1890ff, #0984e3)',
          padding: '24px 16px 20px',
          color: '#fff',
        }}>
          {renderUserInfo()}
        </div>

        {role === 'USER' && (
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
        )}

        <div style={{ background: '#fff', borderRadius: 8, margin: '0 12px', overflow: 'hidden' }}>
          {renderMenuList()}
        </div>

        <div style={{ padding: '16px 12px' }}>
          <Button danger block size="large" onClick={handleLogout}>
            退出登录
          </Button>
        </div>

        {renderModals()}
      </div>
    )
  }

  // 桌面端
  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <Card>
        {renderUserInfo()}

        <Divider style={{ margin: '16px 0' }} />

        {renderMenuList()}

        <Divider style={{ margin: '16px 0' }} />

        <Button danger block onClick={handleLogout}>
          退出登录
        </Button>
      </Card>

      {renderModals()}
    </div>
  )
}
