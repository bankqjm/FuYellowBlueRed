import { Card, Typography, List, Avatar, Space, Button, Tag } from 'antd'
import { UserOutlined, EditOutlined } from '@ant-design/icons'
import { useAuthStore } from '@/stores/authStore'
import { getRoleInfo } from '@/utils/role'

const { Title, Text } = Typography

export default function Profile() {
  const { userInfo, logout } = useAuthStore()
  const roleInfo = getRoleInfo(userInfo?.role)

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space>
          <Avatar size={64} icon={<UserOutlined />} src={userInfo?.avatar} />
          <Title level={4}>{userInfo?.nickname || '用户'}</Title>
        </Space>

        <List size="small">
          <List.Item>
            <Text strong>手机号：</Text>
            <Text>{userInfo?.phone || '未绑定'}</Text>
          </List.Item>
          <List.Item>
            <Text strong>角色：</Text>
            <Tag color={roleInfo.color}>{roleInfo.text}</Tag>
          </List.Item>
        </List>

        <Button icon={<EditOutlined />} block>
          编辑资料
        </Button>

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
