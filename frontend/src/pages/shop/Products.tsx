
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
  Upload,
  Empty,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  ShoppingOutlined,
  UploadOutlined,
  ShopOutlined,
} from '@ant-design/icons'
import { shopApi, ShopInfo, CategoryInfo, ProductInfo } from '../../services/shop'
import { uploadApi } from '../../services/upload'
import { useIsMobile } from '@/hooks/useIsMobile'
import { useNavigate } from 'react-router-dom'

const { TextArea } = Input
const { Option } = Select

export default function Products() {
  const navigate = useNavigate()
  const [shop, setShop] = useState<ShopInfo | null>(null)
  const [categories, setCategories] = useState<CategoryInfo[]>([])
  const [products, setProducts] = useState<ProductInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [hasShop, setHasShop] = useState<boolean | null>(null)

  const [categoryModalVisible, setCategoryModalVisible] = useState(false)
  const [productModalVisible, setProductModalVisible] = useState(false)
  const [editingCategory, setEditingCategory] = useState<CategoryInfo | null>(null)
  const [editingProduct, setEditingProduct] = useState<ProductInfo | null>(null)
  const [productImage, setProductImage] = useState<string>('')

  const [categoryForm] = Form.useForm()
  const [productForm] = Form.useForm()
  const isMobile = useIsMobile()

  const fetchData = async () => {
    try {
      setLoading(true)
      const shopRes = await shopApi.getMyShop()
      setShop(shopRes.data)

      if (shopRes.data) {
        setHasShop(true)
        const categoriesRes = await shopApi.listCategories(shopRes.data.id)
        setCategories(categoriesRes.data)

        const productsRes = await shopApi.listProducts(shopRes.data.id)
        setProducts(productsRes.data.items)
      } else {
        setHasShop(false)
      }
    } catch (error) {
      setHasShop(false)
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
      if (!shop) {return}

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
    setProductImage('')
    setProductModalVisible(true)
  }

  const handleEditProduct = (product: ProductInfo) => {
    setEditingProduct(product)
    productForm.setFieldsValue(product)
    setProductImage(product.image || '')
    setProductModalVisible(true)
  }

  const handleImageUpload = async (file: File) => {
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
      setProductImage(res.data.url)
      productForm.setFieldsValue({ image: res.data.url })
      message.success('图片上传成功')
    } catch {
      message.error('图片上传失败')
    }
    return false
  }

  const handleSaveProduct = async (values: any) => {
    try {
      if (!shop) {return}

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

  const getCategoryName = (categoryId?: number) => {
    if (categoryId === undefined) {return '-'}
    const category = categories.find((c) => c.id === categoryId)
    return category?.name || '-'
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
      render: (categoryId: number) => getCategoryName(categoryId),
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

  const renderMobileCategories = () => (
    <div>
      <div style={{ marginBottom: 12, textAlign: 'right' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAddCategory} size="small">
          添加分类
        </Button>
      </div>
      {categories.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无分类</div>
      ) : (
        categories.map((cat) => (
          <div className="mobile-card" key={cat.id}>
            <div className="card-row">
              <span className="label">分类名称</span>
              <span className="value">{cat.name}</span>
            </div>
            <div className="card-row">
              <span className="label">排序</span>
              <span className="value">{cat.sort_order}</span>
            </div>
            <div className="card-actions">
              <Button size="small" icon={<EditOutlined />} onClick={() => handleEditCategory(cat)}>
                编辑
              </Button>
              <Popconfirm
                title="确定删除这个分类？"
                onConfirm={() => handleDeleteCategory(cat.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
              </Popconfirm>
            </div>
          </div>
        ))
      )}
    </div>
  )

  const renderMobileProducts = () => (
    <div>
      <div style={{ marginBottom: 12, textAlign: 'right' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAddProduct} size="small">
          添加商品
        </Button>
      </div>
      {products.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 32, color: '#999' }}>暂无商品</div>
      ) : (
        products.map((product) => (
          <div className="mobile-card" key={product.id}>
            <div style={{ display: 'flex', gap: 10 }}>
              {product.image ? (
                <Image src={product.image} width={60} height={60} style={{ borderRadius: 6, flexShrink: 0 }} />
              ) : (
                <div style={{
                  width: 60, height: 60, background: '#f0f0f0', borderRadius: 6,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, color: '#999', fontSize: 12,
                }}>
                  商品
                </div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{product.name}</div>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 2 }}>
                  {getCategoryName(product.category_id)}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: '#f5222d', fontWeight: 700, fontSize: 16 }}>
                    ¥{product.price.toFixed(2)}
                  </span>
                  {getStatusText(product.status)}
                </div>
                <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
                  库存: {product.stock} | 销量: {product.sales}
                </div>
              </div>
            </div>
            <div className="card-actions">
              <Button size="small" icon={<EditOutlined />} onClick={() => handleEditProduct(product)}>
                编辑
              </Button>
              <Popconfirm
                title="确定删除这个商品？"
                onConfirm={() => handleDeleteProduct(product.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
              </Popconfirm>
            </div>
          </div>
        ))
      )}
    </div>
  )

  const tabItemsConfig = [
    {
      key: 'products',
      label: <span><ShoppingOutlined /> 商品管理</span>,
      children: isMobile ? renderMobileProducts() : (
        <>
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
        </>
      ),
    },
    {
      key: 'categories',
      label: <span><AppstoreOutlined /> 分类管理</span>,
      children: isMobile ? renderMobileCategories() : (
        <>
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
        </>
      ),
    },
  ]

  if (hasShop === false) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Empty
          image={<ShopOutlined style={{ fontSize: 48, color: '#1890ff' }} />}
          description={
            <div>
              <p style={{ color: '#8c8c8c' }}>欢迎入驻！创建店铺后即可管理商品</p>
              <Button type="primary" onClick={() => navigate('/shop/info')}>创建我的店铺</Button>
            </div>
          }
        />
      </div>
    )
  }

  return (
    <Card>
      <Tabs defaultActiveKey="products" items={tabItemsConfig} />

      <Modal
        title={editingCategory ? '编辑分类' : '添加分类'}
        open={categoryModalVisible}
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
            <InputNumber style={{ width: '100%' }} />
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
        open={productModalVisible}
        onCancel={() => setProductModalVisible(false)}
        footer={null}
        width={isMobile ? undefined : 600}
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
              {categories.map((cat) => (
                <Option key={cat.id} value={cat.id}>
                  {cat.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="商品图片">
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <div>
                {productImage ? (
                  <Image src={productImage} width={100} height={100} style={{ borderRadius: 8 }} />
                ) : (
                  <div style={{
                    width: 100,
                    height: 100,
                    border: '1px dashed #d9d9d9',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#999',
                  }}>
                    未上传
                  </div>
                )}
              </div>
              <div>
                <Upload
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={handleImageUpload}
                >
                  <Button icon={<UploadOutlined />}>上传图片</Button>
                </Upload>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>支持 jpg/png/gif/webp</div>
              </div>
            </div>
            <Input type="hidden" name="image" />
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
