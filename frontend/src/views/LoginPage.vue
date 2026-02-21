<template>
  <div class="auth-page">
    <div class="auth-side"><div class="auth-side-bg"></div>
      <div class="auth-side-content">
        <router-link to="/" class="ab"><span class="brand-icon">N</span>NexusHub</router-link>
        <h1>Welcome<br>back.</h1><p>Sign in to continue building your future.</p>
      </div>
    </div>
    <div class="auth-form-side"><div class="auth-form-wrapper">
      <h2>Sign In</h2><p class="sub">Enter your credentials</p>
      <form @submit.prevent="handleLogin" class="form">
        <div class="input-group"><label>Username</label><input class="input" v-model="form.username" required /></div>
        <div class="input-group"><label>Password</label><input class="input" type="password" v-model="form.password" required /></div>
        <p v-if="err" class="error-msg">{{ err }}</p>
        <button type="submit" class="btn btn-primary btn-lg fw" :disabled="loading">{{ loading ? 'Signing in...' : 'Sign In' }}</button>
      </form>
      <p class="sw">Don't have an account? <router-link to="/register">Create one</router-link></p>
    </div></div>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore(); const loading = ref(false); const err = ref('')
const form = reactive({ username: '', password: '' })
async function handleLogin() { err.value=''; loading.value=true; try { await auth.login(form) } catch(e) { err.value=e.response?.data?.detail||'Invalid credentials' } finally { loading.value=false } }
</script>
<style scoped>
.auth-page{display:grid;grid-template-columns:1fr 1fr;min-height:100vh}
.auth-side{position:relative;display:flex;align-items:flex-end;padding:3rem;overflow:hidden}
.auth-side-bg{position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 30% 50%,rgba(232,168,56,.12) 0%,transparent 70%),linear-gradient(135deg,var(--bg-secondary),var(--bg-primary))}
.auth-side-content{position:relative;z-index:1}
.ab{display:inline-flex;align-items:center;gap:10px;font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:var(--text-primary);text-decoration:none;margin-bottom:3rem}
.brand-icon{display:flex;align-items:center;justify-content:center;width:36px;height:36px;background:var(--accent);color:var(--text-inverse);border-radius:var(--radius-md);font-weight:800;font-size:1.2rem}
.auth-side h1{font-size:3.5rem;margin-bottom:12px}.auth-side p{color:var(--text-secondary);font-size:1.1rem}
.auth-form-side{display:flex;align-items:center;justify-content:center;padding:3rem}
.auth-form-wrapper{width:100%;max-width:400px}.auth-form-wrapper h2{font-size:1.8rem;margin-bottom:6px}
.sub{color:var(--text-secondary);font-size:.9rem;margin-bottom:2rem}.form{display:flex;flex-direction:column;gap:18px}
.fw{width:100%;justify-content:center}
.error-msg{color:var(--danger);font-size:.85rem;background:rgba(248,113,113,.08);padding:10px 14px;border-radius:var(--radius-md);border:1px solid rgba(248,113,113,.15)}
.sw{text-align:center;margin-top:1.5rem;font-size:.9rem;color:var(--text-secondary)}
@media(max-width:768px){.auth-page{grid-template-columns:1fr}.auth-side{display:none}}
</style>
