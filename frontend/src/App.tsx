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
import Wallet from '@/pages/user/Wallet'
import ShopOrders from '@/pages/shop/Orders'
import ShopInfo from '@/pages/shop/ShopInfo'
import ShopDashboard from '@/pages/shop/Dashboard'
import Products from '@/pages/shop/Products'
import RiderOrders from '@/pages/rider/Orders'
import RiderEarnings from '@/pages/rider/Earnings'
import RiderWithdraw from '@/pages/rider/Withdraw'
import AdminDashboard from '@/pages/admin/Dashboard'
import AdminShops from '@/pages/admin/Shops'
import AdminUsers from '@/pages/admin/Users'
import AdminOrders from '@/pages/admin/Orders'
import ReviewPage from '@/pages/user/Review'
import Favorites from '@/pages/user/Favorites'
import Coupons from '@/pages/user/Coupons'
import Support from '@/pages/user/Support'
import './App.css'

function AuthGuard({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, role } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (roles && !roles.includes(role || '')) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/user"
            element={
              <AuthGuard roles={['USER', 'SHOP_OWNER', 'RIDER']}>
                <UserLayout />
              </AuthGuard>
            }
          >
            <Route index element={<UserHome />} />
            <Route path="home" element={<UserHome />} />
            <Route path="shop/:id" element={<ShopDetail />} />
            <Route path="cart" element={<Cart />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:id/pay" element={<Orders />} />
            <Route path="wallet" element={<Wallet />} />
            <Route path="profile" element={<Profile />} />
            <Route path="addresses" element={<Addresses />} />
            <Route path="review/:id" element={<ReviewPage />} />
            <Route path="favorites" element={<Favorites />} />
            <Route path="coupons" element={<Coupons />} />
            <Route path="support" element={<Support />} />
          </Route>
          <Route
            path="/shop"
            element={
              <AuthGuard roles={['SHOP_OWNER']}>
                <ShopLayout />
              </AuthGuard>
            }
          >
            <Route index element={<ShopDashboard />} />
            <Route path="dashboard" element={<ShopDashboard />} />
            <Route path="info" element={<ShopInfo />} />
            <Route path="products" element={<Products />} />
            <Route path="orders" element={<ShopOrders />} />
          </Route>
          <Route
            path="/rider"
            element={
              <AuthGuard roles={['RIDER']}>
                <RiderLayout />
              </AuthGuard>
            }
          >
            <Route index element={<RiderOrders />} />
            <Route path="orders" element={<RiderOrders />} />
            <Route path="earnings" element={<RiderEarnings />} />
            <Route path="withdraw" element={<RiderWithdraw />} />
          </Route>
          <Route
            path="/admin"
            element={
              <AuthGuard roles={['ADMIN']}>
                <AdminLayout />
              </AuthGuard>
            }
          >
            <Route index element={<AdminDashboard />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="shops" element={<AdminShops />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="orders" element={<AdminOrders />} />
          </Route>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
