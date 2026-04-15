<template>
  <div class="page container">
    <header class="page-header"><h1>My Applications</h1></header>
    <div v-if="store.loading" class="apps-list">
      <div v-for="n in 4" :key="n" class="app-card card">
        <SkeletonBlock height="18px" width="60%" />
        <div style="margin-top: 10px;"><SkeletonBlock height="12px" width="40%" /></div>
      </div>
    </div>
    <div v-else-if="store.myApps.length" class="apps-list">
      <button
        v-for="a in store.myApps"
        :key="a.id"
        type="button"
        class="app-card card"
        @click="selected = a"
      >
        <div class="app-header">
          <div class="app-project-link">
            <span class="material-icons-round">folder</span>
            {{ projectTitles[a.project_id] || `Project #${a.project_id}` }}
          </div>
          <StatusBadge :status="a.status" />
        </div>
        <p v-if="a.cover_letter" class="app-letter">{{ a.cover_letter }}</p>
        <div class="app-footer">
          <span class="text-muted">{{ latestSummary(a) }}</span>
          <span class="view-details">View details <span class="material-icons-round">chevron_right</span></span>
        </div>
      </button>
    </div>
    <EmptyState
      v-else
      icon="send"
      title="No applications yet"
      subtitle="Browse projects and apply to get started"
      actionText="Browse Projects"
      actionTo="/projects"
    />

    <ApplicationDetailDrawer
      :application="selected"
      view-as="student"
      @close="selected = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
import ApplicationDetailDrawer from '@/components/ApplicationDetailDrawer.vue'

const store = useApplicationsStore()
const selected = ref(null)
const projectTitles = ref({})

const STATUS_LABELS = {
  invited: 'Invited',
  pending: 'Pending', accepted: 'Accepted', rejected: 'Rejected',
  in_progress: 'In Progress', submitted: 'Submitted',
  revision_requested: 'Revision Requested', approved: 'Approved', completed: 'Completed',
}

function latestSummary(app) {
  if (app.status === 'invited' && app.initiator === 'company') {
    return 'You were invited — awaiting your response'
  }
  const hist = app.status_history || []
  if (!hist.length) return `Applied ${fmtDate(app.created_at)}`
  const latest = hist[hist.length - 1]
  return `Latest: ${STATUS_LABELS[latest.status] || latest.status} · ${fmtDate(latest.timestamp)}`
}

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  await store.fetchMy()
  // Resolve project titles for each application in parallel
  const ids = [...new Set(store.myApps.map(a => a.project_id))]
  const results = await Promise.allSettled(ids.map(id => projectsAPI.get(id)))
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') projectTitles.value[ids[i]] = r.value.data.title
  })
})
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.apps-list { display: flex; flex-direction: column; gap: 12px; }
.app-card {
  padding: 16px;
  text-align: left;
  width: 100%;
  border: 1px solid var(--gray-200);
  background: var(--white);
  cursor: pointer;
  transition: all .15s ease;
  border-radius: var(--radius-lg);
}
.app-card:hover { border-color: var(--gray-300); box-shadow: var(--shadow-sm); }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.app-project-link { display: flex; align-items: center; gap: 6px; color: var(--gray-900); font-weight: 500; font-size: .9375rem; }
.app-project-link .material-icons-round { color: var(--accent); font-size: 18px; }
.app-letter { color: var(--gray-600); font-size: .8125rem; margin-bottom: 10px; line-height: 1.5; }
.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
}
.text-muted { color: var(--gray-500); font-size: .8125rem; }
.view-details {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--accent);
  font-size: .8125rem;
  font-weight: 500;
}
.view-details .material-icons-round { font-size: 16px; }
</style>
