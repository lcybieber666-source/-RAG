import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { jwtDecode } from 'jwt-decode'
import router from '@/router'
import { API_ENDPOINTS } from '@/config/api'

interface User {
  id: number
  username: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  // Initialize auth state
  const initAuth = async () => {
    if (token.value) {
      try {
        // Check if token is expired
        const decoded: any = jwtDecode(token.value)
        if (decoded.exp * 1000 < Date.now()) {
          logout()
          return
        }
        
        // Fetch user info
        await fetchUser()
      } catch (e) {
        logout()
      }
    }
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const res = await axios.get(API_ENDPOINTS.auth.me, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      user.value = res.data
    } catch (e) {
      console.error('Failed to fetch user', e)
      logout()
    }
  }

  const login = async (username: string, password: string) => {
    isLoading.value = true
    error.value = null
    try {
      // Use URLSearchParams for OAuth2PasswordRequestForm
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      
      const res = await axios.post(API_ENDPOINTS.auth.login, params)
      token.value = res.data.access_token
      localStorage.setItem('token', token.value!)
      await fetchUser()
      router.push('/')
    } catch (e: any) {
      error.value = e.response?.data?.detail || '登录失败'
    } finally {
      isLoading.value = false
    }
  }

  const register = async (username: string, password: string) => {
    isLoading.value = true
    error.value = null
    try {
      await axios.post(API_ENDPOINTS.auth.register, { username, password })
      // Auto login after register
      await login(username, password)
    } catch (e: any) {
      error.value = e.response?.data?.detail || '注册失败'
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    initAuth
  }
})
