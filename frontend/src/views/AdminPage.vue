<template>
  <div class="admin-page container">
    <h1>Admin Dashboard</h1>
    <p class="page-subtitle">Platform management and statistics</p>

    <!-- Stats -->
    <div v-if="stats" class="stats-row">
      <div class="stat-card" v-for="s in statCards" :key="s.label">
        <div class="stat-label">{{ s.label }}</div>
        <div class="stat-value">{{ s.value }}</div>
      </div>
    </div>

    <!-- Users table -->
    <section class="admin-section">
      <h2>Users Management</h2>

      <div class="table-wrapper">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="mono">{{ u.id }}</td>
              <td>
                <router-link :to="`/profile/${u.id}`" class="user-link">{{ u.username }}</router-link>
              </td>
              <td class="text-muted">{{ u.email }}</td>
              <td>
                <span class="badge" :class="roleBadge(u.role)">{{ u.role }}</span>
              </td>
              <td>
                <span v-if="u.is_blocked" class="badge badge-danger">Blocked</span>
                <span v-else class="badge badge-success">Active</span>
              </td>
              <td>
                <div class="action-btns">
                  <button
                    class="btn btn-sm"
                    :class="u.is_blocked ? 'btn-primary' : 'btn-danger'"
                    @click="toggleBlock(u)"
                  >
                    {{ u.is_blocked ? 'Unblock' : 'Block' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!users.length" class="empty-state">
        <span class="material-icons-round">people</span>
        <h3>No users found</h3>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToastStore } from '@/stores/toast'
import { adminAPI } from '@/api'

const toast = useToastStore()
const stats = ref(null)
const users = ref([])

const statCards = computed(() => stats.value ? [
  { label: 'Total Users', value: stats.value.total_users },
  { label: 'Students', value: stats.value.total_students },
  { label: 'Companies', value: stats.value.total_companies },
  { label: 'Total Projects', value: stats.value.total_projects },
  { label: 'Applications', value: stats.value.total_applications },
  { label: 'Active Projects', value: stats.value.active_projects },
] : [])

function roleBadge(r) {
  const m = { student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }
  return m[r] || 'badge-info'
}

async function toggleBlock(u) {
  try {
    const { data } = await adminAPI.updateUser(u.id, { is_blocked: !u.is_blocked })
    u.is_blocked = data.is_blocked
    toast.success(u.is_blocked ? 'User blocked' : 'User unblocked')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to update user')
  }
}

onMounted(async () => {
  try {
    const [s, u] = await Promise.all([adminAPI.stats(), adminAPI.users({ skip: 0, limit: 50 })])
    stats.value = s.data
    users.value = u.data
  } catch { /* ignore */ }
})
</script>

<style scoped>
.admin-page { padding: 2rem; }
.page-subtitle { color: var(--text-secondary); margin-bottom: 2rem; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 3rem;
}

.admin-section { margin-bottom: 3rem; }
.admin-section h2 { margin-bottom: 1.2rem; }

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}

.admin-table td {
  padding: 14px 16px;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border);
}

.admin-table tr:last-child td {
  border-bottom: none;
}

.admin-table tr:hover td {
  background: var(--bg-card);
}

.mono { font-family: var(--font-mono); font-size: 0.82rem; color: var(--text-muted); }
.text-muted { color: var(--text-secondary); font-size: 0.85rem; }
.user-link { font-weight: 600; }

.action-btns { display: flex; gap: 6px; }
</style>
