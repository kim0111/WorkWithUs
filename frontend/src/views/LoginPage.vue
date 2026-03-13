<template>
  <div class="auth-page">
    <div class="auth-left">
      <router-link to="/" class="auth-brand">
        <div class="brand-mark">N</div>
        <span>NexusHub</span>
      </router-link>
      <div class="auth-left-content">
        <h1>Welcome back</h1>
        <p>Sign in to continue building your future.</p>
      </div>
    </div>
    <div class="auth-right">
      <div class="auth-form-wrap">
        <h2>Sign In</h2>
        <p class="auth-sub">Enter your credentials</p>
        <form @submit.prevent="handleLogin" class="form">
          <div class="input-group"><label>Username</label><input class="input" v-model="form.username" required /></div>
          <div class="input-group"><label>Password</label><input class="input" type="password" v-model="form.password" required /></div>
          <p v-if="err" class="error-msg">{{ err }}</p>
          <button type="submit" class="btn btn-primary btn-lg full-w" :disabled="loading">{{ loading ? 'Signing in...' : 'Sign In' }}</button>
        </form>
        <p class="auth-switch">Don't have an account? <router-link to="/register">Create one</router-link></p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const loading = ref(false)
const err = ref('')
const form = reactive({ username: '', password: '' })
async function handleLogin() {
  err.value = ''; loading.value = true
  try { await auth.login(form) }
  catch (e) { err.value = e.response?.data?.detail || 'Invalid credentials' }
  finally { loading.value = false }
}
</script>
<style scoped>
.auth-page { display: grid; grid-template-columns: 1fr 1fr; min-height: 100vh; }
.auth-left {
  display: flex; flex-direction: column; padding: 2rem;
  background: var(--white); border-right: 1px solid var(--gray-200);
}
.auth-brand {
  display: inline-flex; align-items: center; gap: 8px;
  font-weight: 600; font-size: .875rem; color: var(--gray-900); text-decoration: none;
}
.brand-mark {
  width: 28px; height: 28px; background: var(--accent); color: white;
  border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .8rem;
}
.auth-left-content { margin-top: auto; padding-bottom: 2rem; }
.auth-left h1 { font-size: 2rem; margin-bottom: 8px; }
.auth-left p { color: var(--gray-500); font-size: .9375rem; }
.auth-right { display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--gray-50); }
.auth-form-wrap { width: 100%; max-width: 380px; }
.auth-form-wrap h2 { font-size: 1.25rem; margin-bottom: 4px; }
.auth-sub { color: var(--gray-500); font-size: .8125rem; margin-bottom: 1.5rem; }
.form { display: flex; flex-direction: column; gap: 14px; }
.full-w { width: 100%; justify-content: center; }
.error-msg {
  color: var(--danger); font-size: .8125rem; background: var(--danger-light);
  padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid #fecaca;
}
.auth-switch { text-align: center; margin-top: 1.25rem; font-size: .8125rem; color: var(--gray-500); }
@media (max-width: 768px) { .auth-page { grid-template-columns: 1fr; } .auth-left { display: none; } }
</style>
