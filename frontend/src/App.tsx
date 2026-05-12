import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useAuthStore } from '@/stores/authStore'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import UserLayout from '@/layouts/UserLayout'
import ShopLayout from '@/layouts/ShopLayout'
import RiderLayout from '@/layouts/RiderLayout'
import AdminLayout from '@/layouts/AdminLayout'
import UserHome from '@/pages/user/Home'
import ShopDetail from '@/pages/user/ShopDetail'
import Cart from '@/pages/user/Cart'
import Orders from '@/pages/user/Orders'
import Profile from '@/pages/user/Profile'
import Addresses from '@/pages/user/Addresses'
import ShopOrders from '@/pages/shop/Orders'
import ShopInfo from '@/pages/shop/ShopInfo'
import Products from '@/pages/shop/Products'
import RiderOrders from '@/pages/rider/Orders'
import AdminDashboard from '@/pages/admin/Dashboard'
import AdminShops from '@/pages/admin/Shops'
import './App.css'

function AuthGuard({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { token, role } = useAuthStore()

  if (!token) {
    return &lt;Navigate to="/login" replace /&gt;
  }

  if (roles &amp;&amp; !roles.includes(role || '')) {
    return &lt;Navigate to="/" replace /&gt;
  }

  return &lt;&gt;{children}&lt;/&gt;
}

function App() {
  return (
    &lt;ConfigProvider locale={zhCN}&gt;
      &lt;BrowserRouter&gt;
        &lt;Routes&gt;
          &lt;Route path="/login" element={&lt;Login /&gt;} /&gt;
          &lt;Route path="/register" element={&lt;Register /&gt;} /&gt;
          &lt;Route
            path="/user"
            element={
              &lt;AuthGuard roles={['USER', 'SHOP_OWNER', 'RIDER']}&gt;
                &lt;UserLayout /&gt;
              &lt;/AuthGuard&gt;
            }
          &gt;
            &lt;Route index element={&lt;UserHome /&gt;} /&gt;
            &lt;Route path="home" element={&lt;UserHome /&gt;} /&gt;
            &lt;Route path="shop/:id" element={&lt;ShopDetail /&gt;} /&gt;
            &lt;Route path="cart" element={&lt;Cart /&gt;} /&gt;
            &lt;Route path="orders" element={&lt;Orders /&gt;} /&gt;
            &lt;Route path="orders/:id/pay" element={&lt;Orders /&gt;} /&gt;
            &lt;Route path="profile" element={&lt;Profile /&gt;} /&gt;
            &lt;Route path="addresses" element={&lt;Addresses /&gt;} /&gt;
          &lt;/Route&gt;
          &lt;Route
            path="/shop"
            element={
              &lt;AuthGuard roles={['SHOP_OWNER']}&gt;
                &lt;ShopLayout /&gt;
              &lt;/AuthGuard&gt;
            }
          &gt;
            &lt;Route index element={&lt;ShopInfo /&gt;} /&gt;
            &lt;Route path="info" element={&lt;ShopInfo /&gt;} /&gt;
            &lt;Route path="products" element={&lt;Products /&gt;} /&gt;
            &lt;Route path="orders" element={&lt;ShopOrders /&gt;} /&gt;
          &lt;/Route&gt;
          &lt;Route
            path="/rider"
            element={
              &lt;AuthGuard roles={['RIDER']}&gt;
                &lt;RiderLayout /&gt;
              &lt;/AuthGuard&gt;
            }
          &gt;
            &lt;Route index element={&lt;RiderOrders /&gt;} /&gt;
            &lt;Route path="orders" element={&lt;RiderOrders /&gt;} /&gt;
          &lt;/Route&gt;
          &lt;Route
            path="/admin"
            element={
              &lt;AuthGuard roles={['ADMIN']}&gt;
                &lt;AdminLayout /&gt;
              &lt;/AuthGuard&gt;
            }
          &gt;
            &lt;Route index element={&lt;AdminDashboard /&gt;} /&gt;
            &lt;Route path="dashboard" element={&lt;AdminDashboard /&gt;} /&gt;
            &lt;Route path="shops" element={&lt;AdminShops /&gt;} /&gt;
          &lt;/Route&gt;
          &lt;Route path="/" element={&lt;Navigate to="/login" replace /&gt;} /&gt;
          &lt;Route path="*" element={&lt;Navigate to="/login" replace /&gt;} /&gt;
        &lt;/Routes&gt;
      &lt;/BrowserRouter&gt;
    &lt;/ConfigProvider&gt;
  )
}

export default App
