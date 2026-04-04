<template>
  <div class="verify-page">
    <div class="verify-card">
      <!-- Loading -->
      <template v-if="loading">
        <div class="verify-icon spinning">
          <span class="material-icons-round">sync</span>
        </div>
        <h2>Verifying your email...</h2>
        <p class="sub">Please wait a moment.</p>
      </template>

      <!-- Success -->
      <template v-else-if="success">
        <div class="verify-icon success">
          <span class="material-icons-round">check_circle</span>
        </div>
        <h2>Email verified!</h2>
        <p class="sub">Your account is now active. You can sign in.</p>
        <router-link to="/login" class="btn btn-primary btn-lg">Sign In</router-link>
      </template>

      <!-- Error -->
      <template v-else>
        <div class="verify-icon error">
          <span class="material-icons-round">error_outline</span>
        </div>
        <h2>Verification failed</h2>
        <p class="sub">{{ errMsg }}</p>
        <router-link to="/register" class="btn btn-primary btn-lg">Register Again</router-link>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const loading = ref(true)
const success = ref(false)
const errMsg = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    loading.value = false
    errMsg.value = 'No verification token provided.'
    return
  }
  try {
    await api.get('/auth/verify-email', { params: { token } })
    success.value = true
  } catch (e) {
    errMsg.value = e.response?.data?.detail || 'Invalid or expired verification link.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.verify-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--gray-50); padding: 2rem;
}
.verify-card {
  text-align: center; background: var(--white); border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg); padding: 3rem 2.5rem; max-width: 420px; width: 100%;
}
.verify-icon {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem;
}
.verify-icon .material-icons-round { font-size: 36px; }
.verify-icon.success { background: #dcfce7; }
.verify-icon.success .material-icons-round { color: #16a34a; }
.verify-icon.error { background: #fef2f2; }
.verify-icon.error .material-icons-round { color: #dc2626; }
.verify-icon.spinning { background: var(--accent-light); }
.verify-icon.spinning .material-icons-round { color: var(--accent); animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.verify-card h2 { font-size: 1.25rem; margin-bottom: 8px; }
.sub { color: var(--gray-500); font-size: .875rem; margin-bottom: 1.5rem; }
.btn { display: inline-flex; text-decoration: none; }
</style>
