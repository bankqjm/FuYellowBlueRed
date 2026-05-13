import { useState, useCallback, useEffect, useMemo } from 'react'
import { cartApi, CartItemInfo } from '../services/order'

export const useCart = () => {
  const [cartItems, setCartItems] = useState<CartItemInfo[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCart = useCallback(async () => {
    try {
      setLoading(true)
      const res = await cartApi.getCart()
      setCartItems(res.data)
    } catch (error) {
      console.error('获取购物车失败', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const addToCart = useCallback(async (productId: number, shopId: number, quantity: number) => {
    try {
      const res = await cartApi.addToCart({ product_id: productId, shop_id: shopId, quantity })
      await fetchCart()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const updateCartItem = useCallback(async (itemId: number, quantity: number) => {
    try {
      const res = await cartApi.updateCartItem(itemId, { quantity })
      await fetchCart()
      return res
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const removeFromCart = useCallback(async (itemId: number) => {
    try {
      await cartApi.deleteCartItem(itemId)
      await fetchCart()
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const clearCartByShop = useCallback(async (shopId: number) => {
    try {
      await cartApi.clearShopCart(shopId)
      await fetchCart()
    } catch (error) {
      throw error
    }
  }, [fetchCart])

  const cartSummary = useMemo(() => {
    const itemsCount = cartItems.reduce((sum, item) => sum + item.quantity, 0)
    const totalPrice = cartItems.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0)
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
