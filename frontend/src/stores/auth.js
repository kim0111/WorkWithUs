import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isStudent = computed(() => user.value?.role === 'student')
  const isCompany = computed(() => user.value?.role === 'company')
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isCommittee = computed(() => user.value?.role === 'committee')

  async function fetchUser() {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      loading.value = true
      const { data } = await authAPI.getMe()
      user.value = data
    } catch {
      logout()
    } finally {
      loading.value = false
    }
  }

  async function login(credentials) {
    const { data } = await authAPI.login(credentials)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function register(payload) {
    await authAPI.register(payload)
    await login({ username: payload.username, password: payload.password })
  }

  function logout() {
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  return {
    user, loading, isAuthenticated, isStudent, isCompany, isAdmin, isCommittee,
    fetchUser, login, register, logout
  }
})
