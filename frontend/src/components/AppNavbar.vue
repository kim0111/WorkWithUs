<template>
  <nav class="navbar">
    <div class="navbar-inner container">
      <router-link to="/dashboard" class="nav-brand">
        <span class="brand-icon">W</span>
        <span class="brand-text">WorkWithUs</span>
      </router-link>

      <div class="nav-links">
        <router-link to="/projects" class="nav-link">
          <span class="material-icons-round">explore</span>
          Projects
        </router-link>
        <router-link v-if="auth.isStudent" to="/my-applications" class="nav-link">
          <span class="material-icons-round">send</span>
          Applications
        </router-link>
        <router-link v-if="auth.isCompany || auth.isAdmin" to="/projects/create" class="nav-link">
          <span class="material-icons-round">add_circle</span>
          New Project
        </router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link">
          <span class="material-icons-round">admin_panel_settings</span>
          Admin
        </router-link>
      </div>

      <div class="nav-right">
        <router-link to="/notifications" class="nav-icon-btn" title="Notifications">
          <span class="material-icons-round">notifications</span>
        </router-link>
        <div class="nav-user" @click="showMenu = !showMenu" ref="menuRef">
          <div class="user-avatar">{{ userInitial }}</div>
          <span class="user-name">{{ auth.user?.username }}</span>
          <span class="material-icons-round">expand_more</span>

          <transition name="fade">
            <div v-if="showMenu" class="dropdown-menu">
              <router-link :to="`/profile/${auth.user?.id}`" class="dropdown-item" @click="showMenu = false">
                <span class="material-icons-round">person</span>
                Profile
              </router-link>
              <router-link to="/dashboard" class="dropdown-item" @click="showMenu = false">
                <span class="material-icons-round">dashboard</span>
                Dashboard
              </router-link>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item danger" @click="handleLogout">
                <span class="material-icons-round">logout</span>
                Sign Out
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const showMenu = ref(false)
const menuRef = ref(null)

const userInitial = computed(() => (auth.user?.full_name || auth.user?.username || 'U')[0].toUpperCase())

function handleLogout() {
  showMenu.value = false
  auth.logout()
}

function handleClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    showMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: rgba(12, 12, 14, 0.85);
  backdrop-filter: blur(20px) saturate(1.2);
  border-bottom: 1px solid var(--border);
  z-index: 100;
}

.navbar-inner {
  display: flex;
  align-items: center;
  height: 100%;
  gap: 40px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-primary);
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--accent);
  color: var(--text-inverse);
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1.2rem;
}

.brand-text {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s var(--ease);
}

.nav-link .material-icons-round {
  font-size: 18px;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--text-primary);
  background: var(--bg-card);
}

.nav-link.router-link-active {
  color: var(--accent);
}

.nav-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  transition: all 0.2s var(--ease);
}

.nav-icon-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: var(--radius-full);
  cursor: pointer;
  position: relative;
  transition: background 0.2s var(--ease);
}

.nav-user:hover {
  background: var(--bg-card);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #d4822a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--text-inverse);
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.nav-user .material-icons-round {
  font-size: 18px;
  color: var(--text-muted);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  padding: 6px;
  min-width: 200px;
  box-shadow: var(--shadow-lg);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.15s var(--ease);
  border: none;
  background: none;
  width: 100%;
  cursor: pointer;
  font-family: var(--font-body);
}

.dropdown-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.dropdown-item .material-icons-round {
  font-size: 18px;
}

.dropdown-item.danger {
  color: var(--danger);
}

.dropdown-item.danger:hover {
  background: rgba(248, 113, 113, 0.08);
}

.dropdown-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

@media (max-width: 768px) {
  .nav-links { display: none; }
  .user-name { display: none; }
}
</style>
