import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const isAuth = computed(() => !!user.value)
  const isStudent = computed(() => user.value?.role === 'student')
  const isCompany = computed(() => user.value?.role === 'company')
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isCommittee = computed(() => user.value?.role === 'committee')

  async function fetchUser() {
    if (!localStorage.getItem('access_token')) return
    try {
      loading.value = true
      const { data } = await authAPI.me()
      user.value = data
    } catch {
      logout(false)
    } finally {
      loading.value = false
    }
  }

  async function login(creds) {
    const { data } = await authAPI.login(creds)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function register(payload) {
    await authAPI.register(payload)
    await login({ username: payload.username, password: payload.password })
  }

  async function logout(callApi = true) {
    if (callApi) {
      try { await authAPI.logout() } catch { /* ignore */ }
    }
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  return { user, loading, isAuth, isStudent, isCompany, isAdmin, isCommittee, fetchUser, login, register, logout }
})
