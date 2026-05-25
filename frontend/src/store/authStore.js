import { create } from 'zustand'
import { authApi } from '../services/api'

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email, password, hospitalSlug = 'default') => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await authApi.login(email, password, hospitalSlug)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      const { data: user } = await authApi.me()
      set({ user, token: data.access_token, isLoading: false })
      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  logout: async () => {
    try { await authApi.logout() } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, token: null })
  },

  fetchMe: async () => {
    if (!get().token) return
    try {
      const { data } = await authApi.me()
      set({ user: data })
    } catch { get().logout() }
  },

  setUser: (user) => set({ user }),
}))

export default useAuthStore
