<template>
  <div v-if="loading" class="loading-page"><div class="spinner"></div></div>

  <div v-else-if="project" class="project-detail container">
    <button class="btn btn-ghost btn-sm back-btn" @click="$router.back()">
      <span class="material-icons-round">arrow_back</span> Back
    </button>

    <div class="detail-grid">
      <!-- Main content -->
      <div class="detail-main">
        <div class="detail-badges">
          <span class="badge" :class="statusBadge">{{ project.status }}</span>
          <span v-if="project.is_student_project" class="badge badge-teal">Student Project</span>
        </div>

        <h1>{{ project.title }}</h1>

        <div class="detail-meta">
          <div class="meta-item">
            <span class="material-icons-round">person</span>
            <router-link :to="`/profile/${project.owner_id}`">View Author</router-link>
          </div>
          <div class="meta-item">
            <span class="material-icons-round">calendar_today</span>
            {{ formatDate(project.created_at) }}
          </div>
          <div class="meta-item" v-if="project.deadline">
            <span class="material-icons-round">event</span>
            Deadline: {{ formatDate(project.deadline) }}
          </div>
        </div>

        <div class="detail-description">
          <h3>Description</h3>
          <p>{{ project.description }}</p>
        </div>

        <div v-if="project.required_skills?.length" class="detail-skills">
          <h3>Required Skills</h3>
          <div class="skills-list">
            <span v-for="s in project.required_skills" :key="s.id" class="skill-tag">{{ s.name }}</span>
          </div>
        </div>

        <!-- Applications list (for project owner) -->
        <div v-if="isOwner && applications.length" class="detail-applications">
          <h3>Applications ({{ applications.length }})</h3>
          <div class="app-list">
            <div v-for="app in applications" :key="app.id" class="app-item card">
              <div class="app-top">
                <router-link :to="`/profile/${app.applicant_id}`" class="app-applicant">
                  Applicant #{{ app.applicant_id }}
                </router-link>
                <span class="badge" :class="appStatusBadge(app.status)">{{ app.status }}</span>
              </div>
              <p v-if="app.cover_letter" class="app-letter">{{ app.cover_letter }}</p>
              <div v-if="app.status === 'pending'" class="app-actions">
                <button class="btn btn-sm btn-primary" @click="updateAppStatus(app.id, 'accepted')">
                  <span class="material-icons-round">check</span> Accept
                </button>
                <button class="btn btn-sm btn-danger" @click="updateAppStatus(app.id, 'rejected')">
                  <span class="material-icons-round">close</span> Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="detail-sidebar">
        <div class="sidebar-card card">
          <div class="sidebar-stat">
            <span class="material-icons-round">group</span>
            <div>
              <div class="sidebar-stat-value">{{ project.max_participants }}</div>
              <div class="sidebar-stat-label">Max Participants</div>
            </div>
          </div>

          <div class="sidebar-divider"></div>

          <!-- Apply button for students -->
          <div v-if="auth.isStudent && project.status === 'open'">
            <div v-if="hasApplied" class="applied-msg">
              <span class="material-icons-round">check_circle</span>
              You've already applied
            </div>
            <div v-else>
              <textarea v-model="coverLetter" class="input" placeholder="Write a cover letter (optional)" rows="4"></textarea>
              <button class="btn btn-primary full-w" style="margin-top: 12px" @click="handleApply" :disabled="applying">
                {{ applying ? 'Applying...' : 'Apply Now' }}
              </button>
            </div>
          </div>

          <!-- Owner actions -->
          <div v-if="isOwner" class="owner-actions">
            <select v-model="newStatus" class="input" @change="handleStatusChange">
              <option value="">Change Status...</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="closed">Closed</option>
            </select>
            <button class="btn btn-danger full-w" style="margin-top: 8px" @click="handleDelete">
              <span class="material-icons-round">delete</span> Delete Project
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { projectsAPI, applicationsAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const project = ref(null)
const applications = ref([])
const loading = ref(true)
const applying = ref(false)
const hasApplied = ref(false)
const coverLetter = ref('')
const newStatus = ref('')

const isOwner = computed(() => auth.user?.id === project.value?.owner_id)

const statusBadge = computed(() => {
  const m = { open: 'badge-success', in_progress: 'badge-warning', closed: 'badge-danger' }
  return m[project.value?.status] || 'badge-info'
})

function appStatusBadge(s) {
  const m = { pending: 'badge-warning', accepted: 'badge-success', rejected: 'badge-danger', completed: 'badge-info' }
  return m[s] || 'badge-info'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function handleApply() {
  applying.value = true
  try {
    await applicationsAPI.apply({ project_id: project.value.id, cover_letter: coverLetter.value || null })
    hasApplied.value = true
    toast.success('Application submitted!')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to apply')
  }
  applying.value = false
}

async function updateAppStatus(appId, status) {
  try {
    await applicationsAPI.updateStatus(appId, { status })
    const app = applications.value.find(a => a.id === appId)
    if (app) app.status = status
    toast.success(`Application ${status}`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to update')
  }
}

async function handleStatusChange() {
  if (!newStatus.value) return
  try {
    await projectsAPI.update(project.value.id, { status: newStatus.value })
    project.value.status = newStatus.value
    toast.success('Status updated')
  } catch (e) {
    toast.error('Failed to update status')
  }
  newStatus.value = ''
}

async function handleDelete() {
  if (!confirm('Delete this project? This cannot be undone.')) return
  try {
    await projectsAPI.delete(project.value.id)
    toast.success('Project deleted')
    router.push('/projects')
  } catch {
    toast.error('Failed to delete')
  }
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.get(route.params.id)
    project.value = data

    if (auth.isAuthenticated && isOwner.value) {
      const { data: apps } = await applicationsAPI.byProject(data.id)
      applications.value = apps
    }

    if (auth.isStudent) {
      try {
        const { data: myApps } = await applicationsAPI.my()
        hasApplied.value = myApps.some(a => a.project_id === data.id)
      } catch { /* ignore */ }
    }
  } catch {
    toast.error('Project not found')
    router.push('/projects')
  }
  loading.value = false
})
</script>

<style scoped>
.project-detail { padding: 2rem; }
.back-btn { margin-bottom: 1.5rem; }

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 32px;
  align-items: start;
}

.detail-badges { display: flex; gap: 8px; margin-bottom: 12px; }

.detail-main h1 {
  font-size: 2.2rem;
  margin-bottom: 16px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.88rem;
  color: var(--text-secondary);
}

.meta-item .material-icons-round { font-size: 18px; color: var(--text-muted); }
.meta-item a { color: var(--accent); }

.detail-description, .detail-skills, .detail-applications {
  margin-bottom: 2rem;
}

.detail-description h3, .detail-skills h3, .detail-applications h3 {
  font-size: 1.1rem;
  margin-bottom: 12px;
}

.detail-description p {
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.app-list { display: flex; flex-direction: column; gap: 12px; }

.app-item { padding: 18px; }
.app-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.app-applicant { font-weight: 600; }
.app-letter { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 12px; }
.app-actions { display: flex; gap: 8px; }

/* Sidebar */
.sidebar-card { position: sticky; top: 90px; }

.sidebar-stat {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sidebar-stat .material-icons-round { font-size: 32px; color: var(--accent); }
.sidebar-stat-value { font-size: 1.5rem; font-weight: 700; font-family: var(--font-display); }
.sidebar-stat-label { font-size: 0.82rem; color: var(--text-muted); }

.sidebar-divider {
  height: 1px;
  background: var(--border);
  margin: 20px 0;
}

.applied-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--success);
  font-weight: 500;
  padding: 12px;
  background: rgba(74, 222, 128, 0.08);
  border-radius: var(--radius-md);
}

.full-w { width: 100%; justify-content: center; }

.owner-actions { display: flex; flex-direction: column; gap: 0; }

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .sidebar-card { position: static; }
}
</style>
