import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserInfo {
  id: number
  phone: string
  nickname?: string
  avatar?: string
  role: string
  status: number
}

interface AuthState {
  isAuthenticated: boolean
  userInfo: UserInfo | null
  role: string | null
  setAuth: (userInfo: UserInfo) => void
  updateUserInfo: (userInfo: Partial<UserInfo>) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      userInfo: null,
      role: null,
      setAuth: (userInfo) =>
        set({
          isAuthenticated: true,
          userInfo,
          role: userInfo.role,
        }),
      updateUserInfo: (partial) =>
        set((state) => ({
          userInfo: state.userInfo ? { ...state.userInfo, ...partial } : null,
        })),
      logout: () =>
        set({
          isAuthenticated: false,
          userInfo: null,
          role: null,
        }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ userInfo: state.userInfo, role: state.role }),
    },
  ),
)
