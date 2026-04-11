<template>
  <div class="student-dash">
    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">Active Applications</div>
        <div class="stat-value">{{ activeCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Completed Projects</div>
        <div class="stat-value">{{ completedCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Average Rating</div>
        <div class="stat-value">
          <template v-if="rating">
            <span class="material-icons-round star-icon">star</span>
            {{ rating.average_rating.toFixed(1) }}
            <span class="stat-sub">({{ rating.total_reviews }})</span>
          </template>
          <template v-else>—</template>
        </div>
      </div>
    </div>

    <!-- My Applications -->
    <section class="dash-section">
      <div class="section-top">
        <h2>My Applications</h2>
        <router-link to="/my-applications" class="btn btn-ghost btn-sm">
          View All<span class="material-icons-round">arrow_forward</span>
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
      <div v-else-if="apps.length" class="dash-list">
        <router-link
          v-for="a in apps"
          :key="a.id"
          :to="`/projects/${a.project_id}`"
          class="dash-list-item dash-list-link"
        >
          <div class="item-content">
            <div class="item-title">{{ projectTitles[a.project_id] || `Project #${a.project_id}` }}</div>
            <span class="item-meta">{{ timeAgo(a.created_at) }}</span>
          </div>
          <StatusBadge :status="a.status" />
        </router-link>
      </div>
      <EmptyState
        v-else
        icon="send"
        title="No applications yet"
        subtitle="Browse projects and apply to get started"
        actionText="Browse Projects"
        actionTo="/projects"
      />
    </section>

    <!-- Suggested Projects -->
    <section class="dash-section">
      <div class="section-top">
        <h2>Open Projects</h2>
        <router-link to="/projects" class="btn btn-ghost btn-sm">
          Browse All<span class="material-icons-round">arrow_forward</span>
        </router-link>
      </div>
      <div v-if="loading" class="grid-2">
        <div v-for="n in 4" :key="n" class="card" style="display: flex; flex-direction: column; gap: 12px;">
          <SkeletonBlock height="20px" width="70%" />
          <SkeletonBlock height="14px" width="40%" />
          <SkeletonBlock height="60px" />
        </div>
      </div>
      <div v-else-if="suggestedProjects.length" class="grid-2">
        <ProjectCard v-for="p in suggestedProjects" :key="p.id" :project="p" />
      </div>
      <EmptyState v-else icon="folder_open" title="No open projects right now" />
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { applicationsAPI, projectsAPI, reviewsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'

const auth = useAuthStore()
const apps = ref([])
const projectTitles = ref({})
const rating = ref(null)
const suggestedProjects = ref([])
const loading = ref(true)

const allApps = ref([])
const activeStatuses = ['pending', 'accepted', 'in_progress', 'submitted', 'revision_requested', 'approved']
const activeCount = computed(() => allApps.value.filter(a => activeStatuses.includes(a.status)).length)
const completedCount = computed(() => allApps.value.filter(a => a.status === 'completed').length)

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

onMounted(async () => {
  try {
    const [appsRes, ratingRes, projectsRes] = await Promise.allSettled([
      applicationsAPI.my(),
      reviewsAPI.rating(auth.user.id),
      projectsAPI.list({ page: 1, size: 4, status: 'open' }),
    ])

    if (appsRes.status === 'fulfilled') {
      allApps.value = appsRes.value.data
      apps.value = allApps.value.slice(0, 5)

      // Resolve project titles in parallel
      const uniqueIds = [...new Set(apps.value.map(a => a.project_id))]
      const titleResults = await Promise.allSettled(
        uniqueIds.map(id => projectsAPI.get(id))
      )
      titleResults.forEach((r, i) => {
        if (r.status === 'fulfilled') {
          projectTitles.value[uniqueIds[i]] = r.value.data.title
        }
      })
    }

    if (ratingRes.status === 'fulfilled') {
      rating.value = ratingRes.value.data
    }

    if (projectsRes.status === 'fulfilled') {
      suggestedProjects.value = projectsRes.value.data.items
    }
  } catch (err) { console.error('DashboardStudentSection load error:', err) } finally {
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
.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-900);
  display: flex;
  align-items: center;
  gap: 4px;
}
.star-icon { font-size: 18px; color: var(--warning); }
.stat-sub { font-size: .75rem; font-weight: 400; color: var(--gray-400); }
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
</style>
