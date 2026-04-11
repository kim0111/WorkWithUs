<template>
  <nav class="navbar">
    <div class="navbar-inner container">
      <router-link to="/dashboard" class="nav-brand">
        <div class="brand-mark">N</div>
        <span class="brand-text">NexusHub</span>
      </router-link>

      <button class="hamburger-btn" @click="drawerOpen = !drawerOpen">
        <span class="material-icons-round">menu</span>
      </button>

      <div class="nav-links">
        <router-link to="/projects" class="nav-link">Projects</router-link>
        <router-link v-if="auth.isStudent" to="/my-applications" class="nav-link">Applications</router-link>
        <router-link v-if="auth.isCompany || auth.isAdmin || auth.isStudent" to="/projects/create" class="nav-link">New Project</router-link>
        <router-link v-if="auth.isAuth" to="/chat" class="nav-link">Chat</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link">Admin</router-link>
      </div>

      <div class="nav-right">
        <button class="nav-icon-btn" @click="theme.toggle()" :title="theme.dark ? 'Switch to light mode' : 'Switch to dark mode'">
          <span class="material-icons-round">{{ theme.dark ? 'light_mode' : 'dark_mode' }}</span>
        </button>
        <router-link to="/notifications" class="nav-icon-btn" title="Notifications">
          <span class="material-icons-round">notifications_none</span>
          <span v-if="unread > 0" class="notif-dot">{{ unread > 9 ? '9+' : unread }}</span>
        </router-link>
        <div class="nav-user" @click="showMenu = !showMenu" ref="menuRef">
          <div class="user-avatar">{{ (auth.user?.full_name || auth.user?.username || 'U')[0].toUpperCase() }}</div>
          <span class="material-icons-round chevron">expand_more</span>
          <transition name="fade">
            <div v-if="showMenu" class="dropdown-menu">
              <router-link :to="`/profile/${auth.user?.id}`" class="dropdown-item" @click="showMenu = false">
                <span class="material-icons-round">person</span>Profile
              </router-link>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item danger" @click="handleLogout">
                <span class="material-icons-round">logout</span>Sign Out
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </nav>

  <Teleport to="body">
    <transition name="drawer">
      <div v-if="drawerOpen" class="drawer-backdrop" @click="drawerOpen = false">
        <div class="drawer-panel" @click.stop>
          <div class="drawer-header">
            <div class="nav-brand">
              <div class="brand-mark">N</div>
              <span class="brand-text">NexusHub</span>
            </div>
            <button class="drawer-close" @click="drawerOpen = false">
              <span class="material-icons-round">close</span>
            </button>
          </div>
          <div class="drawer-links">
            <router-link to="/projects" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">work_outline</span>Projects
            </router-link>
            <router-link v-if="auth.isStudent" to="/my-applications" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">description</span>Applications
            </router-link>
            <router-link v-if="auth.isCompany || auth.isAdmin || auth.isStudent" to="/projects/create" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">add_circle_outline</span>New Project
            </router-link>
            <router-link v-if="auth.isAuth" to="/chat" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">chat_bubble_outline</span>Chat
            </router-link>
            <router-link v-if="auth.isAdmin" to="/admin" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">admin_panel_settings</span>Admin
            </router-link>
          </div>
          <div class="drawer-footer">
            <router-link :to="`/profile/${auth.user?.id}`" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">person</span>Profile
            </router-link>
            <button class="drawer-link danger" @click="drawerOpen = false; handleLogout()">
              <span class="material-icons-round">logout</span>Sign Out
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { notificationsAPI } from '@/api'

const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const showMenu = ref(false)
const menuRef = ref(null)
const unread = ref(0)
const drawerOpen = ref(false)

watch(() => route.path, () => { drawerOpen.value = false })
watch(drawerOpen, (open) => { document.body.style.overflow = open ? 'hidden' : '' })

let interval
onMounted(async () => {
  try { unread.value = (await notificationsAPI.unreadCount()).data.count } catch {}
  interval = setInterval(async () => {
    try { unread.value = (await notificationsAPI.unreadCount()).data.count } catch {}
  }, 30000)
  document.addEventListener('click', onClickOut)
})
onUnmounted(() => {
  clearInterval(interval)
  document.removeEventListener('click', onClickOut)
  document.body.style.overflow = ''
})

function onClickOut(e) { if (menuRef.value && !menuRef.value.contains(e.target)) showMenu.value = false }
function handleLogout() { showMenu.value = false; auth.logout() }
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: 56px;
  background: var(--white); border-bottom: 1px solid var(--gray-200); z-index: 100;
}
.navbar-inner { display: flex; align-items: center; height: 100%; gap: 32px; }
.nav-brand { display: flex; align-items: center; gap: 8px; color: var(--gray-900); text-decoration: none; }
.brand-mark {
  width: 28px; height: 28px; background: var(--accent); color: white;
  border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .8rem;
}
.brand-text { font-size: .9375rem; font-weight: 600; }
.nav-links { display: flex; gap: 2px; }
.nav-link {
  padding: 6px 12px; border-radius: var(--radius-md); color: var(--gray-500);
  font-size: .8125rem; font-weight: 500; text-decoration: none; transition: all .15s ease;
}
.nav-link:hover { color: var(--gray-900); background: var(--gray-100); }
.nav-link.router-link-active { color: var(--accent-text); background: var(--accent-light); }
.nav-right { margin-left: auto; display: flex; align-items: center; gap: 4px; }
.nav-icon-btn {
  position: relative; display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: var(--radius-md); color: var(--gray-500); transition: all .15s ease;
  background: none; border: none; cursor: pointer; font-family: var(--font);
}
.nav-icon-btn:hover { background: var(--gray-100); color: var(--gray-700); }
.notif-dot {
  position: absolute; top: 4px; right: 4px; min-width: 16px; height: 16px;
  background: var(--danger); color: white; font-size: .6rem; font-weight: 600;
  border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 0 3px;
}
.nav-user {
  display: flex; align-items: center; gap: 4px; padding: 4px;
  border-radius: var(--radius-md); cursor: pointer; position: relative; transition: background .15s ease;
}
.nav-user:hover { background: var(--gray-100); }
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: .75rem; color: white;
}
.chevron { font-size: 18px; color: var(--gray-400); }
.dropdown-menu {
  position: absolute; top: calc(100% + 6px); right: 0;
  background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg);
  padding: 4px; min-width: 180px; box-shadow: var(--shadow-lg);
}
.dropdown-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-radius: var(--radius-md); font-size: .8125rem; color: var(--gray-700);
  text-decoration: none; transition: all .1s ease; border: none; background: none;
  width: 100%; cursor: pointer; font-family: var(--font);
}
.dropdown-item:hover { background: var(--gray-100); }
.dropdown-item .material-icons-round { font-size: 16px; color: var(--gray-400); }
.dropdown-item.danger { color: var(--danger); }
.dropdown-item.danger .material-icons-round { color: var(--danger); }
.dropdown-item.danger:hover { background: var(--danger-light); }
.dropdown-divider { height: 1px; background: var(--gray-200); margin: 4px 0; }
.hamburger-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--gray-500);
  cursor: pointer;
}
.hamburger-btn:hover { background: var(--gray-100); color: var(--gray-700); }
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
}
.drawer-panel {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--white);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--gray-200);
}
.drawer-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--gray-500);
  cursor: pointer;
}
.drawer-close:hover { background: var(--gray-100); }
.drawer-links {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.drawer-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--gray-700);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
  font-family: var(--font);
  transition: all 0.15s ease;
}
.drawer-link:hover { background: var(--gray-100); }
.drawer-link.router-link-active { color: var(--accent-text); background: var(--accent-light); }
.drawer-link.danger { color: var(--danger); }
.drawer-link .material-icons-round { font-size: 20px; color: var(--gray-400); }
.drawer-link.danger .material-icons-round { color: var(--danger); }
.drawer-footer {
  padding: 8px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer-panel, .drawer-leave-active .drawer-panel { transition: transform 0.2s ease; }
.drawer-enter-from .drawer-panel, .drawer-leave-to .drawer-panel { transform: translateX(-100%); }
@media (max-width: 768px) {
  .nav-links { display: none; }
  .hamburger-btn { display: flex; }
}
</style>
