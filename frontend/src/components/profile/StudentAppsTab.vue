<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="apps.length" class="apps-list">
        <router-link
          v-for="a in apps"
          :key="a.id"
          :to="`/projects/${a.project_id}`"
          class="app-row card card-interactive"
        >
          <div class="app-row-header">
            <span class="app-project-title">{{ a._projectTitle || `Project #${a.project_id}` }}</span>
            <StatusBadge :status="a.status" />
          </div>
          <p v-if="a.cover_letter" class="app-row-cl">{{ a.cover_letter }}</p>
          <div class="app-row-meta">
            <span class="text-muted">Applied {{ fmtDate(a.created_at) }}</span>
          </div>
        </router-link>
      </div>
      <EmptyState v-else icon="description" title="No applications yet" subtitle="Your project applications will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { applicationsAPI, projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const apps = ref([])
const loading = ref(true)

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await applicationsAPI.my()
    const projectIds = [...new Set(data.map(a => a.project_id))]
    const projectMap = {}
    await Promise.all(
      projectIds.map(async (pid) => {
        try {
          const res = await projectsAPI.get(pid)
          projectMap[pid] = res.data.title
        } catch {}
      })
    )
    apps.value = data.map(a => ({ ...a, _projectTitle: projectMap[a.project_id] || '' }))
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.apps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.app-row {
  padding: 16px;
  text-decoration: none;
  color: inherit;
  display: block;
}
.app-row:hover {
  text-decoration: none;
}
.app-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.app-project-title {
  font-weight: 600;
  font-size: 0.9375rem;
}
.app-row-cl {
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}
.app-row-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.text-muted {
  color: var(--gray-400);
  font-size: 0.8125rem;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
