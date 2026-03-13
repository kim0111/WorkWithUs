<template>
  <div class="page container">
    <header class="page-header"><h1>Admin Dashboard</h1></header>

    <div v-if="stats" class="stats-grid">
      <div v-for="s in statCards" :key="s.label" class="stat-card">
        <div class="stat-icon" :style="{ background: s.bg }"><span class="material-icons-round">{{ s.icon }}</span></div>
        <div>
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <section class="admin-section">
      <div class="section-header-row">
        <h2>Users</h2>
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
                  <button v-if="!u.is_blocked" class="btn btn-outline btn-sm" @click="toggleBlock(u, true)">Block</button>
                  <button v-else class="btn btn-primary btn-sm" @click="toggleBlock(u, false)">Unblock</button>
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
    { label: 'Total Users', value: stats.value.total_users, icon: 'people', bg: 'var(--accent-light)' },
    { label: 'Students', value: stats.value.total_students, icon: 'school', bg: 'var(--success-light)' },
    { label: 'Companies', value: stats.value.total_companies, icon: 'business', bg: 'var(--info-light)' },
    { label: 'Projects', value: stats.value.total_projects, icon: 'folder', bg: 'var(--warning-light)' },
    { label: 'Applications', value: stats.value.total_applications, icon: 'send', bg: '#fef3c7' },
    { label: 'Active Projects', value: stats.value.active_projects, icon: 'trending_up', bg: 'var(--success-light)' },
    { label: 'Chat Messages', value: stats.value.total_chat_messages, icon: 'chat', bg: '#fce7f3' },
    { label: 'Notifications', value: stats.value.total_notifications, icon: 'notifications', bg: '#ede9fe' },
  ]
})

function roleBadge(r) {
  return { student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }[r] || 'badge-info'
}

async function toggleBlock(user, block) {
  try { await adminAPI.updateUser(user.id, { is_blocked: block }); user.is_blocked = block; toast.success(block ? 'User blocked' : 'User unblocked') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

async function changeRole(user, role) {
  try { await adminAPI.updateUser(user.id, { role }); user.role = role; toast.success(`Role changed to ${role}`) }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  try { stats.value = (await adminAPI.stats()).data } catch {}
  try { users.value = (await adminAPI.users()).data } catch {}
})
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-bottom: 2rem; }
.stat-card {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg);
}
.stat-icon {
  width: 38px; height: 38px; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-icon .material-icons-round { font-size: 18px; color: var(--gray-700); }
.stat-value { font-size: 1.125rem; font-weight: 700; color: var(--gray-900); }
.stat-label { font-size: .7rem; color: var(--gray-400); text-transform: uppercase; letter-spacing: .04em; }

.admin-section { margin-bottom: 2rem; }
.section-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
.table-wrap { overflow-x: auto; border: 1px solid var(--gray-200); border-radius: var(--radius-lg); background: var(--white); }
.admin-table { width: 100%; border-collapse: collapse; }
.admin-table th {
  padding: 10px 14px; text-align: left; font-size: .7rem; color: var(--gray-400);
  text-transform: uppercase; letter-spacing: .04em; background: var(--gray-50); border-bottom: 1px solid var(--gray-200);
}
.admin-table td { padding: 10px 14px; border-bottom: 1px solid var(--gray-100); font-size: .8125rem; }
.admin-table tr:last-child td { border-bottom: none; }
.admin-table tr:hover td { background: var(--gray-50); }
.mono { font-size: .75rem; color: var(--gray-400); }
.user-link { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--gray-900); font-weight: 500; }
.av-xs {
  width: 24px; height: 24px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: .65rem; color: white;
}
.table-actions { display: flex; gap: 6px; align-items: center; }
.select-sm { padding: 4px 8px; font-size: .75rem; min-width: 100px; }
</style>
