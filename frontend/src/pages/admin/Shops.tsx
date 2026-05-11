import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, message, Tag, Modal, Descriptions, Image } from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { shopApi, adminApi, ShopInfo } from '@/services/shop'

export default function Shops() {
  const [shops, setShops] = useState&lt;ShopInfo[]&gt;([])
  const [loading, setLoading] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedShop, setSelectedShop] = useState&lt;ShopInfo | null&gt;(null)

  const fetchShops = async () =&gt; {
    try {
      setLoading(true)
      const res = await adminApi.listPendingShops()
      setShops(res.data.items)
    } catch (error) {
      console.error('获取店铺列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() =&gt; {
    fetchShops()
  }, [])

  const handleApprove = async (shopId: number) =&gt; {
    try {
      await adminApi.approveShop(shopId)
      message.success('审核通过')
      fetchShops()
    } catch (error) {
      console.error('审核失败:', error)
    }
  }

  const handleReject = async (shopId: number) =&gt; {
    try {
      await adminApi.rejectShop(shopId)
      message.success('已拒绝')
      fetchShops()
    } catch (error) {
      console.error('拒绝失败:', error)
    }
  }

  const getStatusText = (status: number) =&gt; {
    switch (status) {
      case 0:
        return &lt;Tag color="orange"&gt;待审核&lt;/Tag&gt;
      case 1:
        return &lt;Tag color="green"&gt;已通过&lt;/Tag&gt;
      case -1:
        return &lt;Tag color="red"&gt;已拒绝&lt;/Tag&gt;
      default:
        return &lt;Tag&gt;未知&lt;/Tag&gt;
    }
  }

  const columns = [
    {
      title: '店铺名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '店铺Logo',
      dataIndex: 'logo',
      key: 'logo',
      render: (logo: string) =&gt; logo ? &lt;Image src={logo} width={60} height={60} /&gt; : '-',
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) =&gt; getStatusText(status),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ShopInfo) =&gt; (
        &lt;Space size="small"&gt;
          &lt;Button
            type="link"
            icon={&lt;EyeOutlined /&gt;}
            onClick={() =&gt; {
              setSelectedShop(record)
              setDetailVisible(true)
            }}
          &gt;
            查看
          &lt;/Button&gt;
          {record.status === 0 &amp;&amp; (
            &lt;&gt;
              &lt;Button
                type="primary"
                size="small"
                icon={&lt;CheckOutlined /&gt;}
                onClick={() =&gt; handleApprove(record.id)}
              &gt;
                通过
              &lt;/Button&gt;
              &lt;Button
                danger
                size="small"
                icon={&lt;CloseOutlined /&gt;}
                onClick={() =&gt; handleReject(record.id)}
              &gt;
                拒绝
              &lt;/Button&gt;
            &lt;/&gt;
          )}
        &lt;/Space&gt;
      ),
    },
  ]

  return (
    &lt;Card title="店铺审核"&gt;
      &lt;Table
        columns={columns}
        dataSource={shops}
        rowKey="id"
        loading={loading}
      /&gt;
      &lt;Modal
        title="店铺详情"
        visible={detailVisible}
        onCancel={() =&gt; setDetailVisible(false)}
        footer={null}
        width={600}
      &gt;
        {selectedShop &amp;&amp; (
          &lt;Descriptions column={1}&gt;
            &lt;Descriptions.Item label="店铺名称"&gt;{selectedShop.name}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="店铺Logo"&gt;
              {selectedShop.logo ? (
                &lt;Image src={selectedShop.logo} width={200} /&gt;
              ) : (
                '未设置'
              )}
            &lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="店铺地址"&gt;{selectedShop.address}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="营业时间"&gt;{selectedShop.business_hours || '未设置'}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="店铺公告"&gt;{selectedShop.notice || '未设置'}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="店铺评分"&gt;{selectedShop.rating}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="状态"&gt;{getStatusText(selectedShop.status)}&lt;/Descriptions.Item&gt;
            &lt;Descriptions.Item label="创建时间"&gt;{selectedShop.created_at}&lt;/Descriptions.Item&gt;
          &lt;/Descriptions&gt;
        )}
      &lt;/Modal&gt;
    &lt;/Card&gt;
  )
}
