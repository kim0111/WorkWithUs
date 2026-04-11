<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="apps.length" class="apps-list">
        <div v-for="a in apps" :key="a.id" class="app-row card">
          <div class="app-row-header">
            <router-link :to="`/profile/${a.applicant_id}`" class="applicant-link">
              <div class="av-sm">{{ String(a.applicant_id).charAt(0) }}</div>
              User #{{ a.applicant_id }}
            </router-link>
            <StatusBadge :status="a.status" />
          </div>
          <div class="app-row-meta">
            <span class="project-title">{{ a._projectTitle }}</span>
            <span class="text-muted">&middot; {{ fmtDate(a.created_at) }}</span>
          </div>
          <p v-if="a.cover_letter" class="app-row-cl">{{ a.cover_letter }}</p>
        </div>
      </div>
      <EmptyState v-else icon="inbox" title="No applications yet" subtitle="Applications to your projects will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectsAPI, applicationsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps({
  userId: { type: Number, required: true },
})

const apps = ref([])
const loading = ref(true)

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: props.userId, size: 100 })
    const projects = data.items || []
    const allApps = []

    await Promise.all(
      projects.map(async (p) => {
        try {
          const res = await applicationsAPI.byProject(p.id)
          for (const a of res.data) {
            a._projectTitle = p.title
            allApps.push(a)
          }
        } catch {}
      })
    )

    allApps.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    apps.value = allApps
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
}
.app-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.applicant-link {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--gray-900);
  font-weight: 500;
  font-size: 0.875rem;
}
.av-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.7rem;
  color: white;
}
.app-row-meta {
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 6px;
}
.project-title {
  color: var(--accent-text);
  font-weight: 500;
}
.text-muted {
  color: var(--gray-400);
}
.app-row-cl {
  margin-top: 8px;
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
