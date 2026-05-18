import { useState, useEffect } from 'react'
import { Card, Typography, Form, Input, InputNumber, Button, message, Spin, Space, Divider } from 'antd'
import api from '@/services/api'
import { useIsMobile } from '@/hooks/useIsMobile'

const { Title, Text } = Typography

interface ConfigItem {
  key: string
  value: string
  description: string
}

export default function AdminConfig() {
  const isMobile = useIsMobile()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [configs, setConfigs] = useState<ConfigItem[]>([])
  const [form] = Form.useForm()

  const fetchConfigs = async () => {
    try {
      setLoading(true)
      const res = await api.get('/config')
      const items = res.data || []
      setConfigs(items)
      const formValues: Record<string, string | number> = {}
      for (const item of items) {
        const numVal = Number(item.value)
        formValues[item.key] = isNaN(numVal) ? item.value : numVal
      }
      form.setFieldsValue(formValues)
    } catch (error) {
      console.error('获取配置失败', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleSave = async () => {
    try {
      setSaving(true)
      const values = form.getFieldsValue()
      for (const item of configs) {
        const newValue = String(values[item.key] ?? item.value)
        if (newValue !== item.value) {
          await api.put(`/config/${item.key}`, { value: newValue })
        }
      }
      message.success('配置已保存')
      fetchConfigs()
    } catch (error) {
      message.error('保存失败')
      console.error('保存配置失败', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>
  }

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>平台配置</Title>
          <Button type="primary" onClick={handleSave} loading={saving}>保存配置</Button>
        </div>
      </Card>
      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout={isMobile ? 'vertical' : 'horizontal'} labelCol={{ span: isMobile ? undefined : 6 }} wrapperCol={{ span: isMobile ? undefined : 14 }}>
          {configs.map((item) => {
            const numVal = Number(item.value)
            const isNumeric = !isNaN(numVal) && item.value.trim() !== ''
            return (
              <Form.Item key={item.key} label={item.description || item.key} name={item.key}
                extra={<Text type="secondary" style={{ fontSize: 12 }}>配置键: {item.key}</Text>}>
                {isNumeric ? (
                  <InputNumber style={{ width: '100%' }} min={0} step={item.key.includes('rate') ? 0.01 : 1} />
                ) : (
                  <Input />
                )}
              </Form.Item>
            )
          })}
          {configs.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Text type="secondary">暂无配置项</Text>
            </div>
          )}
        </Form>
      </Card>
    </div>
  )
}
