
import { useEffect, useState } from 'react'
import {
  Card,
  Button,
  Table,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Image,
  Tabs,
  Tag,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  ShoppingOutlined,
} from '@ant-design/icons'
import { shopApi, ShopInfo, CategoryInfo, ProductInfo } from '../../services/shop'

const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

export default function Products() {
  const [shop, setShop] = useState<ShopInfo | null>(null)
  const [categories, setCategories] = useState<CategoryInfo[]>([])
  const [products, setProducts] = useState<ProductInfo[]>([])
  const [loading, setLoading] = useState(true)

  const [categoryModalVisible, setCategoryModalVisible] = useState(false)
  const [productModalVisible, setProductModalVisible] = useState(false)
  const [editingCategory, setEditingCategory] = useState<CategoryInfo | null>(null)
  const [editingProduct, setEditingProduct] = useState<ProductInfo | null>(null)

  const [categoryForm] = Form.useForm()
  const [productForm] = Form.useForm()

  const fetchData = async () => {
    try {
      setLoading(true)
      const shopRes = await shopApi.getMyShop()
      setShop(shopRes.data)

      if (shopRes.data) {
        const categoriesRes = await shopApi.listCategories(shopRes.data.id)
        setCategories(categoriesRes.data)

        const productsRes = await shopApi.listProducts(shopRes.data.id)
        setProducts(productsRes.data.items)
      }
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAddCategory = () => {
    setEditingCategory(null)
    categoryForm.resetFields()
    setCategoryModalVisible(true)
  }

  const handleEditCategory = (category: CategoryInfo) => {
    setEditingCategory(category)
    categoryForm.setFieldsValue(category)
    setCategoryModalVisible(true)
  }

  const handleSaveCategory = async (values: any) => {
    try {
      if (!shop) return

      if (editingCategory) {
        await shopApi.updateCategory(editingCategory.id, values)
        message.success('更新成功')
      } else {
        await shopApi.createCategory({ ...values, shop_id: shop.id })
        message.success('创建成功')
      }
      setCategoryModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('保存分类失败:', error)
    }
  }

  const handleDeleteCategory = async (categoryId: number) => {
    try {
      await shopApi.deleteCategory(categoryId)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除分类失败:', error)
    }
  }

  const handleAddProduct = () => {
    setEditingProduct(null)
    productForm.resetFields()
    setProductModalVisible(true)
  }

  const handleEditProduct = (product: ProductInfo) => {
    setEditingProduct(product)
    productForm.setFieldsValue(product)
    setProductModalVisible(true)
  }

  const handleSaveProduct = async (values: any) => {
    try {
      if (!shop) return

      if (editingProduct) {
        await shopApi.updateProduct(editingProduct.id, values)
        message.success('更新成功')
      } else {
        await shopApi.createProduct({ ...values, shop_id: shop.id })
        message.success('创建成功')
      }
      setProductModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('保存商品失败:', error)
    }
  }

  const handleDeleteProduct = async (productId: number) => {
    try {
      await shopApi.deleteProduct(productId)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除商品失败:', error)
    }
  }

  const getStatusText = (status: number) => {
    return status === 1 ? <Tag color="green">上架</Tag> : <Tag color="gray">下架</Tag>
  }

  const categoryColumns = [
    {
      title: '分类名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: CategoryInfo) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEditCategory(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个分类？"
            onConfirm={() => handleDeleteCategory(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const productColumns = [
    {
      title: '商品图片',
      dataIndex: 'image',
      key: 'image',
      render: (image: string) => image ? <Image src={image} width={60} height={60} /> : '-',
    },
    {
      title: '商品名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分类',
      dataIndex: 'category_id',
      key: 'category_id',
      render: (categoryId: number) => {
        const category = categories.find(c => c.id === categoryId)
        return category?.name || '-'
      },
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '库存',
      dataIndex: 'stock',
      key: 'stock',
    },
    {
      title: '销量',
      dataIndex: 'sales',
      key: 'sales',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => getStatusText(status),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ProductInfo) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEditProduct(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个商品？"
            onConfirm={() => handleDeleteProduct(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card>
      <Tabs defaultActiveKey="products">
        <TabPane
          tab={
            <span>
              <ShoppingOutlined />
              商品管理
            </span>
          }
          key="products"
        >
          <div style={{ marginBottom: 16, textAlign: 'right' }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddProduct}>
              添加商品
            </Button>
          </div>
          <Table
            columns={productColumns}
            dataSource={products}
            rowKey="id"
            loading={loading}
          />
        </TabPane>
        <TabPane
          tab={
            <span>
              <AppstoreOutlined />
              分类管理
            </span>
          }
          key="categories"
        >
          <div style={{ marginBottom: 16, textAlign: 'right' }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddCategory}>
              添加分类
            </Button>
          </div>
          <Table
            columns={categoryColumns}
            dataSource={categories}
            rowKey="id"
            loading={loading}
          />
        </TabPane>
      </Tabs>

      <Modal
        title={editingCategory ? '编辑分类' : '添加分类'}
        visible={categoryModalVisible}
        onCancel={() => setCategoryModalVisible(false)}
        footer={null}
      >
        <Form form={categoryForm} onFinish={handleSaveCategory} layout="vertical">
          <Form.Item
            label="分类名称"
            name="name"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="排序" name="sort_order" initialValue={0}>
            <InputNumber />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => setCategoryModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingProduct ? '编辑商品' : '添加商品'}
        visible={productModalVisible}
        onCancel={() => setProductModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={productForm} onFinish={handleSaveProduct} layout="vertical">
          <Form.Item
            label="商品名称"
            name="name"
            rules={[{ required: true, message: '请输入商品名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="商品分类" name="category_id">
            <Select placeholder="请选择分类">
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>
                  {cat.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="商品图片" name="image">
            <Input placeholder="请输入图片链接" />
          </Form.Item>
          <Form.Item
            label="价格"
            name="price"
            rules={[{ required: true, message: '请输入价格' }]}
          >
            <InputNumber min={0} precision={2} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="原价" name="original_price">
            <InputNumber min={0} precision={2} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="库存" name="stock" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="状态" name="status" initialValue={1}>
            <Select>
              <Option value={1}>上架</Option>
              <Option value={0}>下架</Option>
            </Select>
          </Form.Item>
          <Form.Item label="商品描述" name="description">
            <TextArea rows={4} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => setProductModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

