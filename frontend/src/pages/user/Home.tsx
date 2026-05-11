import { Input, List, Card, Typography, Space, Empty, Spin } from 'antd'
import { SearchOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { useState } from 'react'

const { Title, Text } = Typography

export default function UserHome() {
  const [loading] = useState(false)
  const [searchText] = useState('')

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Input
          size="large"
          placeholder="搜索商家或商品..."
          prefix={<SearchOutlined />}
        />
      </Card>

      <Spin spinning={loading}>
        <List
          locale={{ emptyText: <Empty description="暂无商家信息" /> }}
          renderItem={() => (
            <List.Item>
              <Card hoverable>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Title level={5}>示例商家</Title>
                  <Space>
                    <Text><EnvironmentOutlined /> 示例地址</Text>
                    <Text type="secondary">距离：1.2km</Text>
                  </Space>
                  <Text type="secondary">评分：4.8 | 起送：¥20</Text>
                </Space>
              </Card>
            </List.Item>
          )}
          dataSource={searchText ? [] : []}
        />
      </Spin>

      <div style={{ marginTop: 16 }}>
        <Text type="secondary">* 商家列表和功能将在 M2-M3 阶段完善</Text>
      </div>
    </div>
  )
}
