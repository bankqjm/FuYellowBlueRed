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
  token: string | null
  userInfo: UserInfo | null
  role: string | null
  setAuth: (token: string, userInfo: UserInfo) => void
  updateUserInfo: (userInfo: Partial<UserInfo>) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userInfo: null,
      role: null,
      setAuth: (token, userInfo) =>
        set({
          token,
          userInfo,
          role: userInfo.role,
        }),
      updateUserInfo: (partial) =>
        set((state) => ({
          userInfo: state.userInfo ? { ...state.userInfo, ...partial } : null,
        })),
      logout: () =>
        set({
          token: null,
          userInfo: null,
          role: null,
        }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
