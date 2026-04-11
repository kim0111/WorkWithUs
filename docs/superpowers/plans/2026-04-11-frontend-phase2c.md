# Frontend Phase 2C: Role-Based Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the generic dashboard with role-specific content — students see their applications and suggested projects, companies see their projects and pending applications, admins keep the existing stats view.

**Architecture:** DashboardPage becomes a thin orchestrator. Two new self-loading section components (`DashboardStudentSection`, `DashboardCompanySection`) handle their own data fetching and rendering. Admin content stays inline. Uses existing API modules and components (StatusBadge, ProjectCard, SkeletonBlock, EmptyState).

**Tech Stack:** Vue 3 Composition API, existing API modules, existing component library

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/components/dashboard/DashboardStudentSection.vue` | Student stats, recent applications, suggested projects |
| Create | `frontend/src/components/dashboard/DashboardCompanySection.vue` | Company stats, my projects, pending applications |
| Modify | `frontend/src/views/DashboardPage.vue` | Thin orchestrator with role-conditional rendering |

---

### Task 1: Create DashboardStudentSection

**Files:**
- Create: `frontend/src/components/dashboard/DashboardStudentSection.vue`

- [ ] **Step 1: Create the dashboard directory**

```bash
mkdir -p frontend/src/components/dashboard
```

- [ ] **Step 2: Create the component**

Create `frontend/src/components/dashboard/DashboardStudentSection.vue`:

```vue
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

const activeStatuses = ['pending', 'accepted', 'in_progress', 'submitted', 'revision_requested']
const activeCount = computed(() => apps.value.filter(a => activeStatuses.includes(a.status)).length)
const completedCount = computed(() => apps.value.filter(a => a.status === 'completed').length)

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
      const allApps = appsRes.value.data
      apps.value = allApps.slice(0, 5)

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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/DashboardStudentSection.vue
git commit -m "feat: add DashboardStudentSection with stats, applications, suggested projects"
```

---

### Task 2: Create DashboardCompanySection

**Files:**
- Create: `frontend/src/components/dashboard/DashboardCompanySection.vue`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/dashboard/DashboardCompanySection.vue`:

```vue
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/dashboard/DashboardCompanySection.vue
git commit -m "feat: add DashboardCompanySection with stats, projects, pending applications"
```

---

### Task 3: Rewrite DashboardPage as role-based orchestrator

**Files:**
- Modify: `frontend/src/views/DashboardPage.vue`

This is a full rewrite of the file. The current file is 122 lines. The new version keeps the shared header, conditionally renders role sections, and keeps admin content inline.

- [ ] **Step 1: Rewrite the entire file**

Replace the entire contents of `frontend/src/views/DashboardPage.vue` with:

```vue
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/DashboardPage.vue
git commit -m "refactor: rewrite DashboardPage as role-based orchestrator"
```

---

### Task 4: Build verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run production build**

```bash
cd frontend && npx vite build
```

Expected: Build succeeds with no errors.

- [ ] **Step 2: Commit (only if build required fixes)**

Only commit if you had to fix anything.
