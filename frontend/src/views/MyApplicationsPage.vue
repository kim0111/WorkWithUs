<template>
  <div class="applications-page container">
    <h1>My Applications</h1>
    <p class="page-subtitle">Track the status of your project submissions</p>

    <div v-if="loading" class="loading-page"><div class="spinner"></div></div>

    <template v-else>
      <div v-if="applications.length" class="app-list">
        <div v-for="app in applications" :key="app.id" class="card app-row">
          <div class="app-main">
            <router-link :to="`/projects/${app.project_id}`" class="app-project">
              Project #{{ app.project_id }}
            </router-link>
            <p v-if="app.cover_letter" class="app-cover">{{ app.cover_letter }}</p>
            <span class="app-date">Applied {{ formatDate(app.created_at) }}</span>
          </div>
          <span class="badge" :class="statusBadge(app.status)">{{ app.status }}</span>
        </div>
      </div>

      <div v-else class="empty-state">
        <span class="material-icons-round">inbox</span>
        <h3>No applications yet</h3>
        <p>Browse projects and start applying to showcase your skills.</p>
        <router-link to="/projects" class="btn btn-primary" style="margin-top: 1rem">
          Browse Projects
        </router-link>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { applicationsAPI } from '@/api'

const applications = ref([])
const loading = ref(true)

function statusBadge(s) {
  const m = { pending: 'badge-warning', accepted: 'badge-success', rejected: 'badge-danger', completed: 'badge-info' }
  return m[s] || 'badge-info'
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await applicationsAPI.my()
    applications.value = data
  } catch { /* ignore */ }
  loading.value = false
})
</script>

<style scoped>
.applications-page { padding: 2rem; }
.page-subtitle { color: var(--text-secondary); margin-bottom: 2rem; }

.app-list { display: flex; flex-direction: column; gap: 12px; }

.app-row {
  display: flex; justify-content: space-between; align-items: center;
}

.app-project {
  font-weight: 600; font-size: 1.05rem; display: block; margin-bottom: 4px;
}

.app-cover {
  color: var(--text-secondary); font-size: 0.88rem; margin-bottom: 6px;
  max-width: 600px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.app-date { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono); }
</style>
