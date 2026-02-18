<template>
  <div class="dashboard container">
    <!-- Header -->
    <header class="dash-header">
      <div>
        <p class="dash-greeting">Welcome back,</p>
        <h1>{{ auth.user?.full_name || auth.user?.username }}</h1>
      </div>
      <span class="badge" :class="roleBadge">{{ auth.user?.role }}</span>
    </header>

    <!-- Quick Stats -->
    <div class="stats-row" v-if="stats">
      <div class="stat-card" v-for="s in statCards" :key="s.label">
        <div class="stat-label">{{ s.label }}</div>
        <div class="stat-value">{{ s.value }}</div>
      </div>
    </div>

    <!-- Quick Actions -->
    <section class="dash-section">
      <h2>Quick Actions</h2>
      <div class="actions-grid">
        <router-link v-if="auth.isCompany || auth.isAdmin" to="/projects/create" class="action-card">
          <span class="material-icons-round">add_circle</span>
          <div>
            <h4>Create Project</h4>
            <p>Publish a new project for students</p>
          </div>
        </router-link>
        <router-link to="/projects" class="action-card">
          <span class="material-icons-round">explore</span>
          <div>
            <h4>Browse Projects</h4>
            <p>Discover opportunities</p>
          </div>
        </router-link>
        <router-link v-if="auth.isStudent" to="/my-applications" class="action-card">
          <span class="material-icons-round">send</span>
          <div>
            <h4>My Applications</h4>
            <p>Track your submissions</p>
          </div>
        </router-link>
        <router-link :to="`/profile/${auth.user?.id}`" class="action-card">
          <span class="material-icons-round">person</span>
          <div>
            <h4>My Profile</h4>
            <p>Edit your profile & portfolio</p>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Recent Projects -->
    <section class="dash-section">
      <div class="section-top">
        <h2>Recent Projects</h2>
        <router-link to="/projects" class="btn btn-ghost btn-sm">
          View All <span class="material-icons-round">arrow_forward</span>
        </router-link>
      </div>
      <div v-if="projects.length" class="grid-2">
        <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
      </div>
      <div v-else class="empty-state">
        <span class="material-icons-round">folder_open</span>
        <h3>No projects yet</h3>
        <p>Check back later or create one yourself.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, adminAPI, applicationsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'

const auth = useAuthStore()
const projects = ref([])
const stats = ref(null)
const myAppsCount = ref(0)

const roleBadge = computed(() => {
  const map = { student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }
  return map[auth.user?.role] || 'badge-info'
})

const statCards = computed(() => {
  if (auth.isAdmin && stats.value) {
    return [
      { label: 'Total Users', value: stats.value.total_users },
      { label: 'Active Projects', value: stats.value.active_projects },
      { label: 'Total Projects', value: stats.value.total_projects },
      { label: 'Applications', value: stats.value.total_applications },
    ]
  }
  return [
    { label: 'Projects Found', value: projects.value.length },
    { label: 'My Applications', value: myAppsCount.value },
  ]
})

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ page: 1, size: 4 })
    projects.value = data.items

    if (auth.isAdmin) {
      const { data: s } = await adminAPI.stats()
      stats.value = s
    }

    if (auth.isStudent) {
      const { data: apps } = await applicationsAPI.my()
      myAppsCount.value = apps.length
    }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}

.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}

.dash-greeting {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 2.5rem;
}

.dash-section {
  margin-bottom: 3rem;
}

.dash-section h2 {
  margin-bottom: 1.2rem;
}

.section-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: inherit;
  transition: all 0.25s var(--ease);
}

.action-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.action-card .material-icons-round {
  font-size: 32px;
  color: var(--accent);
}

.action-card h4 {
  font-family: var(--font-body);
  font-weight: 600;
  margin-bottom: 2px;
}

.action-card p {
  font-size: 0.82rem;
  color: var(--text-muted);
}
</style>
