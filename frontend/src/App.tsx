import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import React, { Suspense } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { ThemeProvider } from '@/contexts/ThemeContext'

// PERF-REFORM-03: Layout components remain statically imported (framework, needed on first paint)
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import UserLayout from '@/layouts/UserLayout'
import ShopLayout from '@/layouts/ShopLayout'
import RiderLayout from '@/layouts/RiderLayout'
import AdminLayout from '@/layouts/AdminLayout'

// Page components lazy loaded for code splitting
const UserHome = React.lazy(() => import('@/pages/user/Home'))
const ShopDetail = React.lazy(() => import('@/pages/user/ShopDetail'))
const Cart = React.lazy(() => import('@/pages/user/Cart'))
const Orders = React.lazy(() => import('@/pages/user/Orders'))
const Profile = React.lazy(() => import('@/pages/user/Profile'))
const Addresses = React.lazy(() => import('@/pages/user/Addresses'))
const Wallet = React.lazy(() => import('@/pages/user/Wallet'))
const ShopOrders = React.lazy(() => import('@/pages/shop/Orders'))
const ShopInfo = React.lazy(() => import('@/pages/shop/ShopInfo'))
const ShopDashboard = React.lazy(() => import('@/pages/shop/Dashboard'))
const ShopProducts = React.lazy(() => import('@/pages/shop/Products'))
const ShopEarnings = React.lazy(() => import('@/pages/shop/Earnings'))
const RiderOrders = React.lazy(() => import('@/pages/rider/Orders'))
const RiderEarnings = React.lazy(() => import('@/pages/rider/Earnings'))
const RiderWithdraw = React.lazy(() => import('@/pages/rider/Withdraw'))
const AdminDashboard = React.lazy(() => import('@/pages/admin/Dashboard'))
const AdminShops = React.lazy(() => import('@/pages/admin/Shops'))
const AdminUsers = React.lazy(() => import('@/pages/admin/Users'))
const AdminOrders = React.lazy(() => import('@/pages/admin/Orders'))
const AdminAuditLogs = React.lazy(() => import('@/pages/admin/AuditLogs'))
const AdminConfig = React.lazy(() => import('@/pages/admin/Config'))
const ReviewPage = React.lazy(() => import('@/pages/user/Review'))
const Favorites = React.lazy(() => import('@/pages/user/Favorites'))
const Coupons = React.lazy(() => import('@/pages/user/Coupons'))
const Support = React.lazy(() => import('@/pages/user/Support'))

import './App.css'

/** Suspense fallback shown while lazy-loaded chunks are being fetched */
const LazyFallback = (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" tip="加载中..." />
  </div>
)

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
    <ThemeProvider>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <Suspense fallback={LazyFallback}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
          <Route
            path="/user"
            element={
              <AuthGuard roles={['USER', 'SHOP_OWNER', 'RIDER', 'ADMIN']}>
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
            <Route path="products" element={<ShopProducts />} />
            <Route path="orders" element={<ShopOrders />} />
            <Route path="earnings" element={<ShopEarnings />} />
            <Route path="profile" element={<Profile />} />
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
            <Route path="profile" element={<Profile />} />
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
            <Route path="audit-logs" element={<AdminAuditLogs />} />
            <Route path="config" element={<AdminConfig />} />
            <Route path="profile" element={<Profile />} />
          </Route>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
    </ThemeProvider>
  )
}

export default App
