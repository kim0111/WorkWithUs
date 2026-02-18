<template>
  <div class="auth-page">
    <div class="auth-side">
      <div class="auth-side-content">
        <router-link to="/" class="auth-brand">
          <span class="brand-icon">N</span>
          WorkWithUs
        </router-link>
        <h1>Join the<br>community.</h1>
        <p>Create your account and start collaborating today.</p>
      </div>
      <div class="auth-side-bg"></div>
    </div>

    <div class="auth-form-side">
      <div class="auth-form-wrapper">
        <h2>Create Account</h2>
        <p class="auth-subtitle">Fill in your details to get started</p>

        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="role-selector">
            <button
              v-for="r in roles" :key="r.value"
              type="button"
              class="role-option"
              :class="{ active: form.role === r.value }"
              @click="form.role = r.value"
            >
              <span class="material-icons-round">{{ r.icon }}</span>
              {{ r.label }}
            </button>
          </div>

          <div class="input-group">
            <label>Full Name</label>
            <input class="input" v-model="form.full_name" placeholder="John Doe" />
          </div>

          <div class="row-2">
            <div class="input-group">
              <label>Username</label>
              <input class="input" v-model="form.username" placeholder="johndoe" required />
            </div>
            <div class="input-group">
              <label>Email</label>
              <input class="input" type="email" v-model="form.email" placeholder="john@example.com" required />
            </div>
          </div>

          <div class="input-group">
            <label>Password</label>
            <input class="input" type="password" v-model="form.password" placeholder="Min. 6 characters" required />
          </div>

          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <button type="submit" class="btn btn-primary btn-lg full-w" :disabled="loading">
            <span v-if="loading" class="spinner-sm"></span>
            {{ loading ? 'Creating...' : 'Create Account' }}
          </button>
        </form>

        <p class="auth-switch">
          Already have an account?
          <router-link to="/login">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const errorMsg = ref('')

const roles = [
  { value: 'student', label: 'Student', icon: 'school' },
  { value: 'company', label: 'Company', icon: 'business' },
]

const form = reactive({
  email: '',
  username: '',
  password: '',
  full_name: '',
  role: 'student',
})

async function handleRegister() {
  errorMsg.value = ''
  loading.value = true
  try {
    await auth.register(form)
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
}

.auth-side {
  position: relative;
  display: flex;
  align-items: flex-end;
  padding: 3rem;
  overflow: hidden;
}

.auth-side-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 60% at 60% 40%, rgba(62, 207, 180, 0.1) 0%, transparent 70%),
    linear-gradient(135deg, var(--bg-secondary), var(--bg-primary));
  z-index: 0;
}

.auth-side-content {
  position: relative;
  z-index: 1;
}

.auth-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
  margin-bottom: 3rem;
}

.auth-brand .brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--accent);
  color: var(--text-inverse);
  border-radius: var(--radius-md);
  font-weight: 800;
  font-size: 1.2rem;
}

.auth-side h1 { font-size: 3.5rem; margin-bottom: 12px; }
.auth-side p { color: var(--text-secondary); font-size: 1.1rem; }

.auth-form-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.auth-form-wrapper {
  width: 100%;
  max-width: 460px;
}

.auth-form-wrapper h2 { font-size: 1.8rem; margin-bottom: 6px; }
.auth-subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 2rem; }

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.role-selector {
  display: flex;
  gap: 10px;
}

.role-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: var(--bg-input);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease);
}

.role-option .material-icons-round { font-size: 20px; }

.role-option:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.role-option.active {
  border-color: var(--accent);
  background: var(--accent-dim);
  color: var(--accent);
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.full-w { width: 100%; justify-content: center; }

.error-msg {
  color: var(--danger);
  font-size: 0.85rem;
  background: rgba(248, 113, 113, 0.08);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(248, 113, 113, 0.15);
}

.spinner-sm {
  width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: var(--text-inverse);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.auth-switch {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-side { display: none; }
  .row-2 { grid-template-columns: 1fr; }
}
</style>
