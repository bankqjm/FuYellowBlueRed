
import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Image, Spin, Descriptions, Tag, TimePicker, Checkbox, Upload } from 'antd'
import { ShopOutlined, EditOutlined, SaveOutlined, UploadOutlined } from '@ant-design/icons'
import { shopApi, ShopInfo as ShopInfoType } from '../../services/shop'
import { uploadApi } from '../../services/upload'
import dayjs from 'dayjs'

const { TextArea } = Input

const WEEKDAY_OPTIONS = [
  { label: '周一', value: '1' },
  { label: '周二', value: '2' },
  { label: '周三', value: '3' },
  { label: '周四', value: '4' },
  { label: '周五', value: '5' },
  { label: '周六', value: '6' },
  { label: '周日', value: '7' },
]

export default function ShopInfo() {
  const [shop, setShop] = useState<ShopInfoType | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [logoUrl, setLogoUrl] = useState<string>('')
  const [form] = Form.useForm()

  const fetchShop = async () => {
    try {
      setLoading(true)
      const res = await shopApi.getMyShop()
      setShop(res.data)
      setLogoUrl(res.data?.logo || '')
      form.setFieldsValue({
        ...res.data,
        business_time: res.data?.business_hours
          ? res.data.business_hours.split(' - ').map((t: string) => dayjs(t, 'HH:mm'))
          : undefined,
        business_days: res.data?.business_days
          ? res.data.business_days.split(',')
          : ['1', '2', '3', '4', '5'],
      })
    } catch (error: any) {
      if (error?.response?.data?.message?.includes('还未创建店铺') || error?.response?.data?.message?.includes('还没有')) {
        setShop(null)
      } else {
        console.error('获取店铺信息失败:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShop()
  }, [])

  const handleLogoUpload = async (file: File) => {
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
      setLogoUrl(res.data.url)
      form.setFieldsValue({ logo: res.data.url })
      message.success('图片上传成功')
    } catch {
      message.error('图片上传失败')
    }
    return false
  }

  const handleApply = async (values: any) => {
    try {
      setSubmitting(true)
      const businessHours = values.business_time
        ? `${values.business_time[0].format('HH:mm')} - ${values.business_time[1].format('HH:mm')}`
        : undefined
      const businessDays = values.business_days ? values.business_days.join(',') : undefined

      const data = {
        name: values.name,
        logo: values.logo || logoUrl || undefined,
        address: values.address,
        business_hours: businessHours,
        business_days: businessDays,
        notice: values.notice || undefined,
      }
      const res = await shopApi.apply(data)
      setShop(res.data)
      message.success('申请成功，等待审核')
    } catch (error) {
      console.error('申请店铺失败:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async (values: any) => {
    try {
      setSubmitting(true)
      const businessHours = values.business_time
        ? `${values.business_time[0].format('HH:mm')} - ${values.business_time[1].format('HH:mm')}`
        : undefined
      const businessDays = values.business_days ? values.business_days.join(',') : undefined

      const data = {
        name: values.name,
        logo: values.logo || logoUrl || undefined,
        address: values.address,
        business_hours: businessHours,
        business_days: businessDays,
        notice: values.notice || undefined,
      }
      const res = await shopApi.updateMyShop(data)
      setShop(res.data)
      message.success('更新成功')
      setEditing(false)
    } catch (error) {
      console.error('更新店铺失败:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusText = (status: number) => {
    switch (status) {
      case 0:
        return <Tag color="orange">待审核</Tag>
      case 1:
        return <Tag color="green">营业中</Tag>
      case 2:
        return <Tag color="blue">休息中</Tag>
      case -1:
        return <Tag color="red">已拒绝</Tag>
      default:
        return <Tag>未知</Tag>
    }
  }

  const getBusinessDaysText = (days?: string) => {
    if (!days) return '未设置'
    const dayMap: Record<string, string> = { '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日' }
    return days.split(',').map(d => dayMap[d] || d).join('、')
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!shop) {
    return (
      <Card title="创建店铺">
        <Form form={form} onFinish={handleApply} layout="vertical"
          initialValues={{ business_days: ['1', '2', '3', '4', '5'] }}
        >
          <Form.Item
            label="店铺名称"
            name="name"
            rules={[
              { required: true, message: '请输入店铺名称' },
              { min: 2, message: '店铺名称至少2个字符' },
              { max: 100, message: '店铺名称最多100个字符' },
            ]}
          >
            <Input placeholder="请输入店铺名称" />
          </Form.Item>
          <Form.Item label="店铺Logo" name="logo">
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <div>
                {logoUrl ? (
                  <Image src={logoUrl} width={80} height={80} style={{ borderRadius: 8, objectFit: 'cover' }} />
                ) : (
                  <div style={{
                    width: 80, height: 80, border: '1px dashed #d9d9d9', borderRadius: 8,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999',
                  }}>
                    未上传
                  </div>
                )}
              </div>
              <div>
                <Upload accept="image/*" showUploadList={false} beforeUpload={handleLogoUpload}>
                  <Button icon={<UploadOutlined />}>上传Logo</Button>
                </Upload>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>支持 jpg/png，不超过5MB</div>
              </div>
            </div>
            <Input type="hidden" name="logo" />
          </Form.Item>
          <Form.Item
            label="店铺地址"
            name="address"
            rules={[
              { required: true, message: '请输入店铺地址' },
              { min: 5, message: '地址至少5个字符' },
            ]}
          >
            <Input placeholder="请输入详细地址" />
          </Form.Item>
          <Form.Item label="营业时间" name="business_time">
            <TimePicker.RangePicker format="HH:mm" placeholder={['开始时间', '结束时间']} />
          </Form.Item>
          <Form.Item label="营业日期" name="business_days">
            <Checkbox.Group options={WEEKDAY_OPTIONS} />
          </Form.Item>
          <Form.Item label="店铺公告" name="notice">
            <TextArea rows={4} placeholder="请输入店铺公告" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<ShopOutlined />} loading={submitting}>
              提交申请
            </Button>
          </Form.Item>
        </Form>
      </Card>
    )
  }

  return (
    <Card
      title="店铺信息"
      extra={
        editing ? (
          <Button type="primary" icon={<SaveOutlined />} onClick={() => form.submit()} loading={submitting}>
            保存
          </Button>
        ) : (
          <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>
            编辑
          </Button>
        )
      }
    >
      {editing ? (
        <Form form={form} onFinish={handleUpdate} layout="vertical">
          <Form.Item label="店铺名称" name="name" rules={[{ min: 2, message: '至少2个字符' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="店铺Logo" name="logo">
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <div>
                {logoUrl ? (
                  <Image src={logoUrl} width={80} height={80} style={{ borderRadius: 8, objectFit: 'cover' }} />
                ) : (
                  <div style={{
                    width: 80, height: 80, border: '1px dashed #d9d9d9', borderRadius: 8,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999',
                  }}>
                    未上传
                  </div>
                )}
              </div>
              <div>
                <Upload accept="image/*" showUploadList={false} beforeUpload={handleLogoUpload}>
                  <Button icon={<UploadOutlined />}>上传Logo</Button>
                </Upload>
              </div>
            </div>
            <Input type="hidden" name="logo" />
          </Form.Item>
          <Form.Item label="店铺地址" name="address" rules={[{ min: 5, message: '至少5个字符' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="营业时间" name="business_time">
            <TimePicker.RangePicker format="HH:mm" placeholder={['开始时间', '结束时间']} />
          </Form.Item>
          <Form.Item label="营业日期" name="business_days">
            <Checkbox.Group options={WEEKDAY_OPTIONS} />
          </Form.Item>
          <Form.Item label="店铺公告" name="notice">
            <TextArea rows={4} />
          </Form.Item>
        </Form>
      ) : (
        <Descriptions column={1}>
          <Descriptions.Item label="店铺状态">{getStatusText(shop.status)}</Descriptions.Item>
          <Descriptions.Item label="店铺名称">{shop.name}</Descriptions.Item>
          <Descriptions.Item label="店铺Logo">
            {shop.logo ? <Image src={shop.logo} width={100} style={{ borderRadius: 8 }} /> : '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label="店铺地址">{shop.address}</Descriptions.Item>
          <Descriptions.Item label="营业时间">{shop.business_hours || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="营业日期">{getBusinessDaysText(shop.business_days)}</Descriptions.Item>
          <Descriptions.Item label="店铺公告">{shop.notice || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="店铺评分">{shop.rating} 分</Descriptions.Item>
        </Descriptions>
      )}
    </Card>
  )
}
