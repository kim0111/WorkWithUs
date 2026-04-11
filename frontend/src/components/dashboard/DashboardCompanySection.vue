<template>
  <div class="company-dash">
    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">My Projects</div>
        <div class="stat-value">{{ myProjectsTotal }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Open Positions</div>
        <div class="stat-value">{{ openCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending Applications</div>
        <div class="stat-value">{{ totalPending }}</div>
      </div>
    </div>

    <!-- My Projects -->
    <section class="dash-section">
      <div class="section-top">
        <h2>My Projects</h2>
        <router-link to="/projects/create" class="btn btn-ghost btn-sm">
          <span class="material-icons-round">add</span>New Project
        </router-link>
      </div>
      <div v-if="loading" class="dash-list">
        <div v-for="n in 5" :key="n" class="dash-list-item" style="pointer-events: none;">
          <div style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
            <SkeletonBlock height="14px" width="50%" />
            <SkeletonBlock height="11px" width="30%" />
          </div>
          <SkeletonBlock height="22px" width="70px" border-radius="var(--radius-full)" />
        </div>
      </div>
      <div v-else-if="myProjects.length" class="dash-list">
        <router-link
          v-for="p in myProjects"
          :key="p.id"
          :to="`/projects/${p.id}`"
          class="dash-list-item dash-list-link"
        >
          <div class="item-content">
            <div class="item-title">{{ p.title }}</div>
            <span class="item-meta">{{ appCounts[p.id] || 0 }} applications &middot; {{ fmtDate(p.created_at) }}</span>
          </div>
          <StatusBadge :status="p.status" />
        </router-link>
      </div>
      <EmptyState
        v-else
        icon="work_outline"
        title="No projects yet"
        subtitle="Create your first project to start receiving applications"
        actionText="Create Project"
        actionTo="/projects/create"
      />
    </section>

    <!-- Pending Applications -->
    <section class="dash-section">
      <div class="section-top">
        <h2>Pending Applications</h2>
        <span v-if="totalPending > 0" class="badge badge-accent">{{ totalPending }}</span>
      </div>
      <div v-if="loading" class="dash-list">
        <div v-for="n in 5" :key="n" class="dash-list-item" style="pointer-events: none;">
          <div style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
            <SkeletonBlock height="14px" width="60%" />
            <SkeletonBlock height="11px" width="35%" />
          </div>
          <SkeletonBlock height="24px" width="60px" border-radius="var(--radius-md)" />
        </div>
      </div>
      <div v-else-if="pendingApps.length" class="dash-list">
        <router-link
          v-for="a in pendingApps"
          :key="a.id"
          :to="`/projects/${a.project_id}`"
          class="dash-list-item dash-list-link"
        >
          <div class="item-content">
            <div class="item-title">User #{{ a.applicant_id }} applied to {{ projectTitles[a.project_id] || `Project #${a.project_id}` }}</div>
            <span class="item-meta">{{ timeAgo(a.created_at) }}</span>
          </div>
          <span class="btn btn-primary btn-sm review-btn">Review</span>
        </router-link>
      </div>
      <EmptyState v-else icon="inbox" title="No pending applications" subtitle="Applications will appear here when students apply to your projects" />
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, applicationsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'

const auth = useAuthStore()
const myProjects = ref([])
const myProjectsTotal = ref(0)
const appCounts = ref({})
const pendingApps = ref([])
const totalPending = ref(0)
const projectTitles = ref({})
const loading = ref(true)

const openCount = computed(() => myProjects.value.filter(p => p.status === 'open').length)

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: auth.user.id, page: 1, size: 5 })
    myProjects.value = data.items
    myProjectsTotal.value = data.total

    // Build project titles map
    myProjects.value.forEach(p => { projectTitles.value[p.id] = p.title })

    // Fetch applications for each project in parallel
    const appResults = await Promise.allSettled(
      myProjects.value.map(p => applicationsAPI.byProject(p.id))
    )

    let allPending = []
    appResults.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        const projectApps = r.value.data
        appCounts.value[myProjects.value[i].id] = projectApps.length
        const pending = projectApps.filter(a => a.status === 'pending')
        allPending.push(...pending)
      }
    })

    allPending.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    totalPending.value = allPending.length
    pendingApps.value = allPending.slice(0, 5)
  } catch {} finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 2rem;
}
.stat-card {
  padding: 16px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
}
.stat-label { font-size: .75rem; color: var(--gray-500); margin-bottom: 4px; }
.stat-value { font-size: 1.25rem; font-weight: 700; color: var(--gray-900); }
.dash-section { margin-bottom: 2.5rem; }
.dash-section h2 { margin-bottom: 1rem; }
.section-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.dash-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dash-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
}
.dash-list-link {
  text-decoration: none;
  color: inherit;
  transition: all 0.15s ease;
  cursor: pointer;
}
.dash-list-link:hover {
  border-color: var(--gray-300);
  box-shadow: var(--shadow-sm);
}
.item-content { flex: 1; min-width: 0; }
.item-title {
  font-weight: 500;
  font-size: .875rem;
  color: var(--gray-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta { font-size: .7rem; color: var(--gray-400); }
.review-btn { pointer-events: none; }
</style>
