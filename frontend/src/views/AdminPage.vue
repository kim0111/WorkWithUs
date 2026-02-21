<template>
  <div class="page container">
    <header class="page-header"><h1><span class="material-icons-round hdr-icon">admin_panel_settings</span>Admin Dashboard</h1></header>

    <!-- Stats -->
    <div v-if="stats" class="stats-grid">
      <div v-for="s in statCards" :key="s.label" class="stat-card">
        <div class="stat-icon" :style="{ background: s.bg }"><span class="material-icons-round">{{ s.icon }}</span></div>
        <div><div class="stat-value">{{ s.value }}</div><div class="stat-label">{{ s.label }}</div></div>
      </div>
    </div>

    <!-- Users Table -->
    <section class="admin-section">
      <div class="section-header-row">
        <h2>Users Management</h2>
        <span class="badge badge-info">{{ users.length }} loaded</span>
      </div>
      <div class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="mono">{{ u.id }}</td>
              <td>
                <router-link :to="`/profile/${u.id}`" class="user-link">
                  <div class="av-xs">{{ (u.full_name || u.username)[0].toUpperCase() }}</div>
                  {{ u.username }}
                </router-link>
              </td>
              <td class="mono">{{ u.email }}</td>
              <td><span class="badge" :class="roleBadge(u.role)">{{ u.role }}</span></td>
              <td>
                <span v-if="u.is_blocked" class="badge badge-danger">Blocked</span>
                <span v-else class="badge badge-success">Active</span>
              </td>
              <td>
                <div class="table-actions">
                  <button v-if="!u.is_blocked" class="btn btn-outline btn-sm" @click="toggleBlock(u, true)">
                    <span class="material-icons-round">block</span>Block
                  </button>
                  <button v-else class="btn btn-primary btn-sm" @click="toggleBlock(u, false)">
                    <span class="material-icons-round">check_circle</span>Unblock
                  </button>
                  <select class="input select-sm" :value="u.role" @change="changeRole(u, $event.target.value)">
                    <option value="student">student</option>
                    <option value="company">company</option>
                    <option value="committee">committee</option>
                    <option value="admin">admin</option>
                  </select>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminAPI } from '@/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const stats = ref(null)
const users = ref([])

const statCards = computed(() => {
  if (!stats.value) return []
  return [
    { label: 'Total Users', value: stats.value.total_users, icon: 'people', bg: 'var(--accent-dim)' },
    { label: 'Students', value: stats.value.total_students, icon: 'school', bg: 'var(--teal-dim)' },
    { label: 'Companies', value: stats.value.total_companies, icon: 'business', bg: 'rgba(96,165,250,.12)' },
    { label: 'Projects', value: stats.value.total_projects, icon: 'folder', bg: 'rgba(192,132,252,.12)' },
    { label: 'Applications', value: stats.value.total_applications, icon: 'send', bg: 'rgba(251,191,36,.12)' },
    { label: 'Active Projects', value: stats.value.active_projects, icon: 'trending_up', bg: 'rgba(74,222,128,.12)' },
    { label: 'Chat Messages', value: stats.value.total_chat_messages, icon: 'chat', bg: 'rgba(244,114,182,.12)' },
    { label: 'Notifications', value: stats.value.total_notifications, icon: 'notifications', bg: 'rgba(167,139,250,.12)' },
  ]
})

function roleBadge(r) {
  return { student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }[r] || 'badge-info'
}

async function toggleBlock(user, block) {
  try {
    await adminAPI.updateUser(user.id, { is_blocked: block })
    user.is_blocked = block
    toast.success(block ? 'User blocked' : 'User unblocked')
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

async function changeRole(user, role) {
  try {
    await adminAPI.updateUser(user.id, { role })
    user.role = role
    toast.success(`Role changed to ${role}`)
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  try { stats.value = (await adminAPI.stats()).data } catch {}
  try { users.value = (await adminAPI.users()).data } catch {}
})
</script>

<style scoped>
.page { padding: 2rem; }
.hdr-icon { font-size: 28px; color: var(--accent); vertical-align: middle; margin-right: 8px; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin-bottom: 2.5rem; }
.stat-card { display: flex; align-items: center; gap: 14px; padding: 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); transition: all .2s var(--ease); }
.stat-card:hover { border-color: var(--border-strong); transform: translateY(-2px); }
.stat-icon { width: 44px; height: 44px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-icon .material-icons-round { font-size: 22px; color: var(--text-primary); }
.stat-value { font-family: var(--font-display); font-size: 1.4rem; font-weight: 700; }
.stat-label { font-size: .78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }

.admin-section { margin-bottom: 2rem; }
.section-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius-lg); }
.admin-table { width: 100%; border-collapse: collapse; }
.admin-table th { padding: 12px 16px; text-align: left; font-size: .78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.admin-table td { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: .9rem; }
.admin-table tr:last-child td { border-bottom: none; }
.admin-table tr:hover td { background: rgba(255,255,255,.02); }
.mono { font-family: var(--font-mono); font-size: .82rem; }
.user-link { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--text-primary); font-weight: 500; }
.av-xs { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #d4822a); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .7rem; color: var(--text-inverse); }
.table-actions { display: flex; gap: 8px; align-items: center; }
.select-sm { padding: 6px 10px; font-size: .82rem; min-width: 110px; }
</style>
