<template>
  <div class="dashboard container">
    <header class="dash-header">
      <div>
        <p class="dash-greeting">Welcome back,</p>
        <h1>{{ auth.user?.full_name || auth.user?.username }}</h1>
      </div>
      <span class="badge" :class="roleBadge">{{ auth.user?.role }}</span>
    </header>

    <DashboardStudentSection v-if="auth.isStudent" />
    <DashboardCompanySection v-else-if="auth.isCompany" />

    <!-- Admin dashboard (inline) -->
    <template v-else-if="auth.isAdmin">
      <div v-if="stats" class="stats-row">
        <div class="stat-card" v-for="s in adminStats" :key="s.label">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ s.value }}</div>
        </div>
      </div>

      <section class="dash-section">
        <h2>Quick Actions</h2>
        <div class="actions-grid">
          <router-link to="/admin" class="action-card">
            <span class="material-icons-round">admin_panel_settings</span>
            <div><h4>Admin Panel</h4><p>Manage users & settings</p></div>
          </router-link>
          <router-link to="/projects/create" class="action-card">
            <span class="material-icons-round">add_circle_outline</span>
            <div><h4>New Project</h4><p>Publish a project</p></div>
          </router-link>
          <router-link to="/projects" class="action-card">
            <span class="material-icons-round">search</span>
            <div><h4>Browse Projects</h4><p>View all projects</p></div>
          </router-link>
          <router-link to="/chat" class="action-card">
            <span class="material-icons-round">chat_bubble_outline</span>
            <div><h4>Messages</h4><p>Chat with users</p></div>
          </router-link>
        </div>
      </section>

      <section class="dash-section">
        <div class="section-top">
          <h2>Recent Projects</h2>
          <router-link to="/projects" class="btn btn-ghost btn-sm">View All<span class="material-icons-round">arrow_forward</span></router-link>
        </div>
        <div v-if="projectsLoading" class="grid-2">
          <div v-for="n in 4" :key="n" class="card" style="display: flex; flex-direction: column; gap: 12px;">
            <SkeletonBlock height="20px" width="70%" />
            <SkeletonBlock height="14px" width="40%" />
            <SkeletonBlock height="60px" />
          </div>
        </div>
        <div v-else-if="projects.length" class="grid-2">
          <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
        </div>
        <div v-else class="empty-state">
          <span class="material-icons-round">folder_open</span>
          <h3>No projects yet</h3>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, adminAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import DashboardStudentSection from '@/components/dashboard/DashboardStudentSection.vue'
import DashboardCompanySection from '@/components/dashboard/DashboardCompanySection.vue'

const auth = useAuthStore()

const roleBadge = computed(() => ({
  student: 'badge-teal',
  company: 'badge-accent',
  admin: 'badge-danger',
  committee: 'badge-info',
}[auth.user?.role] || 'badge-info'))

// Admin-only state
const stats = ref(null)
const projects = ref([])
const projectsLoading = ref(true)

const adminStats = computed(() => {
  if (!stats.value) return []
  return [
    { label: 'Users', value: stats.value.total_users },
    { label: 'Projects', value: stats.value.total_projects },
    { label: 'Applications', value: stats.value.total_applications },
    { label: 'Chat Messages', value: stats.value.total_chat_messages },
  ]
})

onMounted(async () => {
  if (!auth.isAdmin) return
  try { projects.value = (await projectsAPI.list({ page: 1, size: 4 })).data.items } catch {}
  finally { projectsLoading.value = false }
  try { stats.value = (await adminAPI.stats()).data } catch {}
})
</script>

<style scoped>
.dashboard { padding: 2rem 24px; }
.dash-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--gray-200);
}
.dash-greeting { font-size: .8125rem; color: var(--gray-400); margin-bottom: 2px; }
.stats-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 2rem; }
.stat-card { padding: 16px; background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg); }
.stat-label { font-size: .75rem; color: var(--gray-500); margin-bottom: 4px; }
.stat-value { font-size: 1.25rem; font-weight: 700; color: var(--gray-900); }
.dash-section { margin-bottom: 2.5rem; }
.dash-section h2 { margin-bottom: 1rem; }
.section-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.actions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.action-card {
  display: flex; align-items: center; gap: 12px; padding: 16px;
  background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg);
  text-decoration: none; color: inherit; transition: all .15s ease;
}
.action-card:hover { border-color: var(--gray-300); box-shadow: var(--shadow-sm); }
.action-card .material-icons-round { font-size: 24px; color: var(--accent); }
.action-card h4 { font-weight: 500; font-size: .875rem; margin-bottom: 1px; }
.action-card p { font-size: .75rem; color: var(--gray-400); }
</style>
