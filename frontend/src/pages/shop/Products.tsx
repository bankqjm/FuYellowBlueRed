
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
  const [shop, setShop] = useState&lt;ShopInfo | null&gt;(null)
  const [categories, setCategories] = useState&lt;CategoryInfo[]&gt;([])
  const [products, setProducts] = useState&lt;ProductInfo[]&gt;([])
  const [loading, setLoading] = useState(true)

  const [categoryModalVisible, setCategoryModalVisible] = useState(false)
  const [productModalVisible, setProductModalVisible] = useState(false)
  const [editingCategory, setEditingCategory] = useState&lt;CategoryInfo | null&gt;(null)
  const [editingProduct, setEditingProduct] = useState&lt;ProductInfo | null&gt;(null)

  const [categoryForm] = Form.useForm()
  const [productForm] = Form.useForm()

  const fetchData = async () =&gt; {
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

  useEffect(() =&gt; {
    fetchData()
  }, [])

  const handleAddCategory = () =&gt; {
    setEditingCategory(null)
    categoryForm.resetFields()
    setCategoryModalVisible(true)
  }

  const handleEditCategory = (category: CategoryInfo) =&gt; {
    setEditingCategory(category)
    categoryForm.setFieldsValue(category)
    setCategoryModalVisible(true)
  }

  const handleSaveCategory = async (values: any) =&gt; {
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

  const handleDeleteCategory = async (categoryId: number) =&gt; {
    try {
      await shopApi.deleteCategory(categoryId)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除分类失败:', error)
    }
  }

  const handleAddProduct = () =&gt; {
    setEditingProduct(null)
    productForm.resetFields()
    setProductModalVisible(true)
  }

  const handleEditProduct = (product: ProductInfo) =&gt; {
    setEditingProduct(product)
    productForm.setFieldsValue(product)
    setProductModalVisible(true)
  }

  const handleSaveProduct = async (values: any) =&gt; {
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

  const handleDeleteProduct = async (productId: number) =&gt; {
    try {
      await shopApi.deleteProduct(productId)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除商品失败:', error)
    }
  }

  const getStatusText = (status: number) =&gt; {
    return status === 1 ? &lt;Tag color="green"&gt;上架&lt;/Tag&gt; : &lt;Tag color="gray"&gt;下架&lt;/Tag&gt;
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
      render: (_: any, record: CategoryInfo) =&gt; (
        &lt;Space size="small"&gt;
          &lt;Button type="link" icon={&lt;EditOutlined /&gt;} onClick={() =&gt; handleEditCategory(record)}&gt;
            编辑
          &lt;/Button&gt;
          &lt;Popconfirm
            title="确定删除这个分类？"
            onConfirm={() =&gt; handleDeleteCategory(record.id)}
            okText="确定"
            cancelText="取消"
          &gt;
            &lt;Button type="link" danger icon={&lt;DeleteOutlined /&gt;}&gt;
              删除
            &lt;/Button&gt;
          &lt;/Popconfirm&gt;
        &lt;/Space&gt;
      ),
    },
  ]

  const productColumns = [
    {
      title: '商品图片',
      dataIndex: 'image',
      key: 'image',
      render: (image: string) =&gt; image ? &lt;Image src={image} width={60} height={60} /&gt; : '-',
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
      render: (categoryId: number) =&gt; {
        const category = categories.find(c =&gt; c.id === categoryId)
        return category?.name || '-'
      },
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) =&gt; `¥${price.toFixed(2)}`,
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
      render: (status: number) =&gt; getStatusText(status),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ProductInfo) =&gt; (
        &lt;Space size="small"&gt;
          &lt;Button type="link" icon={&lt;EditOutlined /&gt;} onClick={() =&gt; handleEditProduct(record)}&gt;
            编辑
          &lt;/Button&gt;
          &lt;Popconfirm
            title="确定删除这个商品？"
            onConfirm={() =&gt; handleDeleteProduct(record.id)}
            okText="确定"
            cancelText="取消"
          &gt;
            &lt;Button type="link" danger icon={&lt;DeleteOutlined /&gt;}&gt;
              删除
            &lt;/Button&gt;
          &lt;/Popconfirm&gt;
        &lt;/Space&gt;
      ),
    },
  ]

  return (
    &lt;Card&gt;
      &lt;Tabs defaultActiveKey="products"&gt;
        &lt;TabPane
          tab={
            &lt;span&gt;
              &lt;ShoppingOutlined /&gt;
              商品管理
            &lt;/span&gt;
          }
          key="products"
        &gt;
          &lt;div style={{ marginBottom: 16, textAlign: 'right' }}&gt;
            &lt;Button type="primary" icon={&lt;PlusOutlined /&gt;} onClick={handleAddProduct}&gt;
              添加商品
            &lt;/Button&gt;
          &lt;/div&gt;
          &lt;Table
            columns={productColumns}
            dataSource={products}
            rowKey="id"
            loading={loading}
          /&gt;
        &lt;/TabPane&gt;
        &lt;TabPane
          tab={
            &lt;span&gt;
              &lt;AppstoreOutlined /&gt;
              分类管理
            &lt;/span&gt;
          }
          key="categories"
        &gt;
          &lt;div style={{ marginBottom: 16, textAlign: 'right' }}&gt;
            &lt;Button type="primary" icon={&lt;PlusOutlined /&gt;} onClick={handleAddCategory}&gt;
              添加分类
            &lt;/Button&gt;
          &lt;/div&gt;
          &lt;Table
            columns={categoryColumns}
            dataSource={categories}
            rowKey="id"
            loading={loading}
          /&gt;
        &lt;/TabPane&gt;
      &lt;/Tabs&gt;

      &lt;Modal
        title={editingCategory ? '编辑分类' : '添加分类'}
        visible={categoryModalVisible}
        onCancel={() =&gt; setCategoryModalVisible(false)}
        footer={null}
      &gt;
        &lt;Form form={categoryForm} onFinish={handleSaveCategory} layout="vertical"&gt;
          &lt;Form.Item
            label="分类名称"
            name="name"
            rules={[{ required: true, message: '请输入分类名称' }]}
          &gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="排序" name="sort_order" initialValue={0}&gt;
            &lt;InputNumber /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item&gt;
            &lt;Space&gt;
              &lt;Button type="primary" htmlType="submit"&gt;
                保存
              &lt;/Button&gt;
              &lt;Button onClick={() =&gt; setCategoryModalVisible(false)}&gt;取消&lt;/Button&gt;
            &lt;/Space&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;
      &lt;/Modal&gt;

      &lt;Modal
        title={editingProduct ? '编辑商品' : '添加商品'}
        visible={productModalVisible}
        onCancel={() =&gt; setProductModalVisible(false)}
        footer={null}
        width={600}
      &gt;
        &lt;Form form={productForm} onFinish={handleSaveProduct} layout="vertical"&gt;
          &lt;Form.Item
            label="商品名称"
            name="name"
            rules={[{ required: true, message: '请输入商品名称' }]}
          &gt;
            &lt;Input /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="商品分类" name="category_id"&gt;
            &lt;Select placeholder="请选择分类"&gt;
              {categories.map(cat =&gt; (
                &lt;Option key={cat.id} value={cat.id}&gt;
                  {cat.name}
                &lt;/Option&gt;
              ))}
            &lt;/Select&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="商品图片" name="image"&gt;
            &lt;Input placeholder="请输入图片链接" /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item
            label="价格"
            name="price"
            rules={[{ required: true, message: '请输入价格' }]}
          &gt;
            &lt;InputNumber min={0} precision={2} style={{ width: '100%' }} /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="原价" name="original_price"&gt;
            &lt;InputNumber min={0} precision={2} style={{ width: '100%' }} /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="库存" name="stock" initialValue={0}&gt;
            &lt;InputNumber min={0} style={{ width: '100%' }} /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="状态" name="status" initialValue={1}&gt;
            &lt;Select&gt;
              &lt;Option value={1}&gt;上架&lt;/Option&gt;
              &lt;Option value={0}&gt;下架&lt;/Option&gt;
            &lt;/Select&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item label="商品描述" name="description"&gt;
            &lt;TextArea rows={4} /&gt;
          &lt;/Form.Item&gt;
          &lt;Form.Item&gt;
            &lt;Space&gt;
              &lt;Button type="primary" htmlType="submit"&gt;
                保存
              &lt;/Button&gt;
              &lt;Button onClick={() =&gt; setProductModalVisible(false)}&gt;取消&lt;/Button&gt;
            &lt;/Space&gt;
          &lt;/Form.Item&gt;
        &lt;/Form&gt;
      &lt;/Modal&gt;
    &lt;/Card&gt;
  )
}

