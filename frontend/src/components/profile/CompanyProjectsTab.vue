<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="projects.length" class="projects-list">
        <router-link
          v-for="p in projects"
          :key="p.id"
          :to="`/projects/${p.id}`"
          class="project-row card card-interactive"
        >
          <div class="project-row-main">
            <div class="project-row-info">
              <div class="project-row-title">
                <span class="project-name">{{ p.title }}</span>
                <StatusBadge :status="p.status" />
              </div>
              <div class="project-row-meta">
                {{ p.max_participants }} spots &middot;
                <template v-if="p.deadline">Deadline: {{ fmtDate(p.deadline) }} &middot;</template>
                {{ applicationCounts[p.id] || 0 }} applications
              </div>
            </div>
            <span class="material-icons-round project-arrow">chevron_right</span>
          </div>
        </router-link>
      </div>
      <EmptyState v-else icon="folder_open" title="No projects yet" subtitle="Projects created by this company will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps({
  userId: { type: Number, required: true },
  isOwner: { type: Boolean, default: false },
})

const applicationsStore = useApplicationsStore()
const projects = ref([])
const loading = ref(true)

const applicationCounts = computed(() => {
  const counts = {}
  projects.value.forEach(p => {
    counts[p.id] = (applicationsStore.byProject[p.id] || []).length
  })
  return counts
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: props.userId, size: 100 })
    projects.value = data.items || []

    if (props.isOwner) {
      await Promise.all(
        projects.value.map(p => applicationsStore.fetchByProject(p.id))
      )
    }
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.projects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.project-row {
  text-decoration: none;
  color: inherit;
  padding: 16px 20px;
}
.project-row:hover {
  text-decoration: none;
}
.project-row-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.project-row-info {
  flex: 1;
}
.project-row-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.project-name {
  font-weight: 600;
  font-size: 0.9375rem;
}
.project-row-meta {
  color: var(--gray-400);
  font-size: 0.8125rem;
  margin-top: 4px;
}
.project-arrow {
  color: var(--gray-400);
  font-size: 20px;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
