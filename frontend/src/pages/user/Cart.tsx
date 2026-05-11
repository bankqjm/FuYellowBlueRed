import { Card, Typography, Empty } from 'antd'

const { Title } = Typography

export default function Cart() {
  return (
    <Card>
      <Empty description="购物车为空" />
      <div style={{ marginTop: 16, textAlign: 'center', color: '#999' }}>
        <Text type="secondary">* 购物车功能将在 M3 阶段完善</Text>
      </div>
    </Card>
  )
}
