import { useState, useCallback, useEffect } from 'react'
import { orderApi } from '../services/order'

export interface CartItem {
  id: number
  product_id: number
  product_name: string
  product_image?: string
  product_price: number
  quantity: number
}

export const useCart = () => {
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCart = useCallback(async () => {
    try {
      setLoading(true)
      const res = await orderApi.getCart()
      setCartItems(res.data)
    } catch (error) {
      console.error('获取购物车失败', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const addToCart = useCallback(async (productId: number, shopId: number, quantity: number) => {
    try {
      const res = await orderApi.addToCart({ product_id: productId, shop_id: shopId, quantity })
      await fetchCart()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const updateCartItem = useCallback(async (itemId: number, quantity: number) => {
    try {
      const res = await orderApi.updateCart(itemId, { quantity })
      await fetchCart()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const removeFromCart = useCallback(async (itemId: number) => {
    try {
      await orderApi.deleteCart(itemId)
      await fetchCart()
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const clearCartByShop = useCallback(async (shopId: number) => {
    try {
      await orderApi.clearShopCart(shopId)
      await fetchCart()
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const cartSummary = useMemo(() => {
    const itemsCount = cartItems.reduce((sum, item) => sum + item.quantity, 0)
    const totalPrice = cartItems.reduce((sum, item) => sum + item.product_price * item.quantity, 0)
    return { itemsCount, totalPrice }
  }, [cartItems])

  useEffect(() => {
    fetchCart()
  }, [fetchCart])

  return {
    cartItems,
    loading,
    fetchCart,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCartByShop,
    ...cartSummary,
  }
}
