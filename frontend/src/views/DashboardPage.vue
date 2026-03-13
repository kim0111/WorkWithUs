<template>
  <div class="dashboard container">
    <header class="dash-header">
      <div>
        <p class="dash-greeting">Welcome back,</p>
        <h1>{{ auth.user?.full_name || auth.user?.username }}</h1>
      </div>
      <span class="badge" :class="rb">{{ auth.user?.role }}</span>
    </header>

    <div v-if="stats" class="stats-row">
      <div class="stat-card" v-for="s in sc" :key="s.l">
        <div class="stat-label">{{ s.l }}</div>
        <div class="stat-value">{{ s.v }}</div>
      </div>
    </div>

    <section class="dash-section">
      <h2>Quick Actions</h2>
      <div class="actions-grid">
        <router-link v-if="auth.isCompany || auth.isAdmin" to="/projects/create" class="action-card">
          <span class="material-icons-round">add_circle_outline</span>
          <div><h4>New Project</h4><p>Publish a project</p></div>
        </router-link>
        <router-link to="/projects" class="action-card">
          <span class="material-icons-round">search</span>
          <div><h4>Browse Projects</h4><p>Discover opportunities</p></div>
        </router-link>
        <router-link to="/chat" class="action-card">
          <span class="material-icons-round">chat_bubble_outline</span>
          <div><h4>Messages</h4><p>Chat with collaborators</p></div>
        </router-link>
        <router-link v-if="auth.isStudent" to="/my-applications" class="action-card">
          <span class="material-icons-round">send</span>
          <div><h4>My Applications</h4><p>Track submissions</p></div>
        </router-link>
        <router-link :to="`/profile/${auth.user?.id}`" class="action-card">
          <span class="material-icons-round">person_outline</span>
          <div><h4>Profile</h4><p>Edit profile & portfolio</p></div>
        </router-link>
      </div>
    </section>

    <section class="dash-section">
      <div class="section-top">
        <h2>Recent Projects</h2>
        <router-link to="/projects" class="btn btn-ghost btn-sm">View All<span class="material-icons-round">arrow_forward</span></router-link>
      </div>
      <div v-if="projects.length" class="grid-2">
        <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
      </div>
      <div v-else class="empty-state">
        <span class="material-icons-round">folder_open</span>
        <h3>No projects yet</h3>
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
const myApps = ref(0)

const rb = computed(() => ({ student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }[auth.user?.role] || 'badge-info'))
const sc = computed(() => {
  if (auth.isAdmin && stats.value) return [
    { l: 'Users', v: stats.value.total_users },
    { l: 'Projects', v: stats.value.total_projects },
    { l: 'Applications', v: stats.value.total_applications },
    { l: 'Chat Messages', v: stats.value.total_chat_messages },
  ]
  return [{ l: 'Projects', v: projects.value.length }, { l: 'My Applications', v: myApps.value }]
})

onMounted(async () => {
  try { projects.value = (await projectsAPI.list({ page: 1, size: 4 })).data.items } catch {}
  if (auth.isAdmin) { try { stats.value = (await adminAPI.stats()).data } catch {} }
  if (auth.isStudent) { try { myApps.value = (await applicationsAPI.my()).data.length } catch {} }
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
