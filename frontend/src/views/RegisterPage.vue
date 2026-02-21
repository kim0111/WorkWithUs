<template>
  <div class="auth-page">
    <div class="auth-side"><div class="auth-side-bg"></div>
      <div class="asc"><router-link to="/" class="ab"><span class="bi">N</span>NexusHub</router-link>
        <h1>Join the<br>community.</h1><p>Create your account and start collaborating.</p></div>
    </div>
    <div class="afs"><div class="afw">
      <h2>Create Account</h2><p class="sub">Fill in your details to get started</p>
      <form @submit.prevent="go" class="form">
        <div class="role-sel">
          <button v-for="r in roles" :key="r.value" type="button" class="ro" :class="{active:form.role===r.value}" @click="form.role=r.value">
            <span class="material-icons-round">{{r.icon}}</span>{{r.label}}
          </button>
        </div>
        <div class="input-group"><label>Full Name</label><input class="input" v-model="form.full_name" /></div>
        <div class="row2">
          <div class="input-group"><label>Username</label><input class="input" v-model="form.username" required /></div>
          <div class="input-group"><label>Email</label><input class="input" type="email" v-model="form.email" required /></div>
        </div>
        <div class="input-group"><label>Password</label><input class="input" type="password" v-model="form.password" required /></div>
        <p v-if="err" class="error-msg">{{err}}</p>
        <button type="submit" class="btn btn-primary btn-lg fw" :disabled="loading">{{loading?'Creating...':'Create Account'}}</button>
      </form>
      <p class="sw">Already have an account? <router-link to="/login">Sign in</router-link></p>
    </div></div>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
const auth=useAuthStore(); const loading=ref(false); const err=ref('')
const roles=[{value:'student',label:'Student',icon:'school'},{value:'company',label:'Company',icon:'business'}]
const form=reactive({email:'',username:'',password:'',full_name:'',role:'student'})
async function go(){err.value='';loading.value=true;try{await auth.register(form)}catch(e){err.value=e.response?.data?.detail||'Failed'}finally{loading.value=false}}
</script>
<style scoped>
.auth-page{display:grid;grid-template-columns:1fr 1fr;min-height:100vh}
.auth-side{position:relative;display:flex;align-items:flex-end;padding:3rem;overflow:hidden}
.auth-side-bg{position:absolute;inset:0;background:radial-gradient(ellipse 60% 60% at 60% 40%,rgba(62,207,180,.1) 0%,transparent 70%),linear-gradient(135deg,var(--bg-secondary),var(--bg-primary))}
.asc{position:relative;z-index:1}.ab{display:inline-flex;align-items:center;gap:10px;font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:var(--text-primary);text-decoration:none;margin-bottom:3rem}
.bi{display:flex;align-items:center;justify-content:center;width:36px;height:36px;background:var(--accent);color:var(--text-inverse);border-radius:var(--radius-md);font-weight:800;font-size:1.2rem}
.auth-side h1{font-size:3.5rem;margin-bottom:12px}.auth-side p{color:var(--text-secondary);font-size:1.1rem}
.afs{display:flex;align-items:center;justify-content:center;padding:3rem}.afw{width:100%;max-width:460px}
.afw h2{font-size:1.8rem;margin-bottom:6px}.sub{color:var(--text-secondary);font-size:.9rem;margin-bottom:2rem}
.form{display:flex;flex-direction:column;gap:18px}
.role-sel{display:flex;gap:10px}
.ro{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;background:var(--bg-input);border:1.5px solid var(--border);border-radius:var(--radius-md);color:var(--text-secondary);font-family:var(--font-body);font-size:.9rem;font-weight:500;cursor:pointer;transition:all .2s var(--ease)}
.ro .material-icons-round{font-size:20px}.ro:hover{border-color:var(--border-strong);color:var(--text-primary)}
.ro.active{border-color:var(--accent);background:var(--accent-dim);color:var(--accent)}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.fw{width:100%;justify-content:center}
.error-msg{color:var(--danger);font-size:.85rem;background:rgba(248,113,113,.08);padding:10px 14px;border-radius:var(--radius-md);border:1px solid rgba(248,113,113,.15)}
.sw{text-align:center;margin-top:1.5rem;font-size:.9rem;color:var(--text-secondary)}
@media(max-width:768px){.auth-page{grid-template-columns:1fr}.auth-side{display:none}.row2{grid-template-columns:1fr}}
</style>
