<template>
  <div class="auth-page">
    <div class="auth-left">
      <router-link to="/" class="auth-brand">
        <div class="brand-mark">N</div>
        <span>NexusHub</span>
      </router-link>
      <div class="auth-left-content">
        <h1>Join the community</h1>
        <p>Create your account and start collaborating.</p>
      </div>
    </div>
    <div class="auth-right">
      <!-- Registration form -->
      <div v-if="!registeredUser" class="auth-form-wrap">
        <h2>Create Account</h2>
        <p class="auth-sub">Fill in your details to get started</p>
        <form @submit.prevent="go" class="form">
          <div class="role-select">
            <button v-for="r in roles" :key="r.value" type="button" class="role-btn" :class="{ active: form.role === r.value }" @click="form.role = r.value">
              <span class="material-icons-round">{{ r.icon }}</span>{{ r.label }}
            </button>
          </div>
          <div class="input-group"><label>Full Name</label><input class="input" v-model="form.full_name" /></div>
          <div class="row-2">
            <div class="input-group"><label>Username</label><input class="input" v-model="form.username" required /></div>
            <div class="input-group"><label>Email</label><input class="input" type="email" v-model="form.email" required /></div>
          </div>
          <div class="input-group"><label>Password</label><input class="input" type="password" v-model="form.password" required /></div>
          <p v-if="err" class="error-msg">{{ err }}</p>
          <button type="submit" class="btn btn-primary btn-lg full-w" :disabled="loading">{{ loading ? 'Creating...' : 'Create Account' }}</button>
        </form>
        <p class="auth-switch">Already have an account? <router-link to="/login">Sign in</router-link></p>
      </div>

      <!-- Verify email prompt (shown when verification is required) -->
      <div v-else-if="registeredUser && !registeredUser.is_active" class="auth-form-wrap verify-prompt">
        <div class="verify-icon">
          <span class="material-icons-round">mark_email_unread</span>
        </div>
        <h2>Check your email</h2>
        <p class="auth-sub">We sent a verification link to <strong>{{ form.email }}</strong>. Click the link to activate your account.</p>
        <div class="verify-tips">
          <p>Didn't receive the email?</p>
          <ul>
            <li>Check your spam or junk folder</li>
            <li>Make sure <strong>{{ form.email }}</strong> is correct</li>
          </ul>
        </div>
        <router-link to="/login" class="btn btn-primary btn-lg full-w">Go to Sign In</router-link>
      </div>

      <!-- Success (verification not required) -->
      <div v-else class="auth-form-wrap verify-prompt">
        <div class="verify-icon">
          <span class="material-icons-round">check_circle</span>
        </div>
        <h2>Account created</h2>
        <p class="auth-sub">Your account is ready. Sign in to continue.</p>
        <router-link to="/login" class="btn btn-primary btn-lg full-w">Go to Sign In</router-link>
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
const registeredUser = ref(null)
const roles = [{ value: 'student', label: 'Student', icon: 'school' }, { value: 'company', label: 'Company', icon: 'business' }]
const form = reactive({ email: '', username: '', password: '', full_name: '', role: 'student' })
async function go() {
  err.value = ''; loading.value = true
  try {
    registeredUser.value = await auth.register(form)
  }
  catch (e) { err.value = e.response?.data?.detail || 'Failed' }
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
.auth-form-wrap { width: 100%; max-width: 440px; }
.auth-form-wrap h2 { font-size: 1.25rem; margin-bottom: 4px; }
.auth-sub { color: var(--gray-500); font-size: .8125rem; margin-bottom: 1.5rem; }
.form { display: flex; flex-direction: column; gap: 14px; }
.role-select { display: flex; gap: 8px; }
.role-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px; background: var(--white); border: 1px solid var(--gray-300);
  border-radius: var(--radius-md); color: var(--gray-600); font-family: var(--font);
  font-size: .8125rem; font-weight: 500; cursor: pointer; transition: all .15s ease;
}
.role-btn .material-icons-round { font-size: 18px; }
.role-btn:hover { border-color: var(--gray-400); }
.role-btn.active { border-color: var(--accent); background: var(--accent-light); color: var(--accent-text); }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.full-w { width: 100%; justify-content: center; }
.error-msg {
  color: var(--danger); font-size: .8125rem; background: var(--danger-light);
  padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid #fecaca;
}
.auth-switch { text-align: center; margin-top: 1.25rem; font-size: .8125rem; color: var(--gray-500); }
.verify-prompt { text-align: center; }
.verify-icon {
  width: 64px; height: 64px; border-radius: 50%; background: var(--accent-light);
  display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem;
}
.verify-icon .material-icons-round { font-size: 32px; color: var(--accent); }
.verify-prompt h2 { margin-bottom: 8px; }
.verify-prompt .auth-sub { margin-bottom: 1.5rem; }
.verify-tips {
  text-align: left; background: var(--white); border: 1px solid var(--gray-200);
  border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 1.5rem; font-size: .8125rem;
}
.verify-tips p { color: var(--gray-600); font-weight: 500; margin-bottom: 6px; }
.verify-tips ul { margin: 0; padding-left: 18px; color: var(--gray-500); }
.verify-tips li { margin-bottom: 2px; }
@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; } .auth-left { display: none; }
  .row-2 { grid-template-columns: 1fr; }
}
</style>
