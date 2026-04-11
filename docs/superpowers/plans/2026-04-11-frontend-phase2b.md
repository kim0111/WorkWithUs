# Frontend Phase 2B: Pinia Data Stores & Skeleton Loaders — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize project and notification data into Pinia stores, replace spinner loading states with skeleton loaders, and refactor 5 views + 1 component to consume store data.

**Architecture:** Two new Pinia stores (notifications, projects) using the Composition API pattern already established by `auth.js` and `toast.js`. One new SkeletonBlock component. Views are refactored to delegate API calls to stores while keeping page-specific UI state local.

**Tech Stack:** Vue 3 Composition API, Pinia, existing CSS design system variables

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/components/SkeletonBlock.vue` | Animated placeholder block with configurable dimensions |
| Create | `frontend/src/stores/notifications.js` | Notification state, polling, CRUD actions |
| Create | `frontend/src/stores/projects.js` | Project list/detail state, CRUD actions |
| Modify | `frontend/src/components/AppNavbar.vue` | Replace inline notification polling with store |
| Modify | `frontend/src/views/NotificationsPage.vue` | Use notifications store + skeleton loader |
| Modify | `frontend/src/views/ProjectsPage.vue` | Use projects store + skeleton loader |
| Modify | `frontend/src/views/ProjectDetailPage.vue` | Use projects store for fetch/update/delete + skeleton |
| Modify | `frontend/src/views/CreateProjectPage.vue` | Use projects store for create |
| Modify | `frontend/src/views/DashboardPage.vue` | Add skeleton loader for recent projects |

---

### Task 1: Create SkeletonBlock component

**Files:**
- Create: `frontend/src/components/SkeletonBlock.vue`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/SkeletonBlock.vue`:

```vue
<template>
  <div
    class="skeleton-block"
    :style="{ width, height, borderRadius }"
  />
</template>

<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '16px' },
  borderRadius: { type: String, default: 'var(--radius-md)' },
})
</script>

<style scoped>
.skeleton-block {
  background: var(--gray-200);
  background-image: linear-gradient(
    90deg,
    var(--gray-200) 0%,
    var(--gray-100) 40%,
    var(--gray-200) 80%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SkeletonBlock.vue
git commit -m "feat: add SkeletonBlock reusable component"
```

---

### Task 2: Create notifications store

**Files:**
- Create: `frontend/src/stores/notifications.js`

- [ ] **Step 1: Create the store**

Create `frontend/src/stores/notifications.js`:

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsAPI } from '@/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)

  async function fetchUnreadCount() {
    try {
      unreadCount.value = (await notificationsAPI.unreadCount()).data.count
    } catch {}
  }

  async function fetchList(unreadOnly = false) {
    loading.value = true
    try {
      items.value = (await notificationsAPI.list(unreadOnly)).data
    } catch {} finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    try {
      await notificationsAPI.markRead(id)
      const item = items.value.find(n => n.id === id)
      if (item && !item.is_read) {
        item.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {}
  }

  async function markAllRead() {
    try {
      await notificationsAPI.markAllRead()
      items.value.forEach(n => { n.is_read = true })
      unreadCount.value = 0
    } catch {}
  }

  let pollInterval = null

  function startPolling() {
    if (pollInterval) return
    fetchUnreadCount()
    pollInterval = setInterval(fetchUnreadCount, 30000)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  return {
    items, unreadCount, loading,
    fetchUnreadCount, fetchList, markRead, markAllRead,
    startPolling, stopPolling,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/notifications.js
git commit -m "feat: add notifications Pinia store with polling"
```

---

### Task 3: Create projects store

**Files:**
- Create: `frontend/src/stores/projects.js`

- [ ] **Step 1: Create the store**

Create `frontend/src/stores/projects.js`:

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsAPI } from '@/api'

export const useProjectsStore = defineStore('projects', () => {
  const items = ref([])
  const total = ref(0)
  const currentProject = ref(null)
  const loading = ref(false)
  const detailLoading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await projectsAPI.list(params)
      items.value = data.items
      total.value = data.total
    } catch {} finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    detailLoading.value = true
    try {
      currentProject.value = (await projectsAPI.get(id)).data
    } catch {
      currentProject.value = null
      throw new Error('Project not found')
    } finally {
      detailLoading.value = false
    }
  }

  async function create(data) {
    const res = await projectsAPI.create(data)
    return res.data
  }

  async function update(id, data) {
    const res = await projectsAPI.update(id, data)
    if (currentProject.value && currentProject.value.id === Number(id)) {
      Object.assign(currentProject.value, res.data)
    }
    return res.data
  }

  async function remove(id) {
    await projectsAPI.delete(id)
    if (currentProject.value && currentProject.value.id === Number(id)) {
      currentProject.value = null
    }
  }

  return {
    items, total, currentProject, loading, detailLoading,
    fetchList, fetchOne, create, update, remove,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/projects.js
git commit -m "feat: add projects Pinia store"
```

---

### Task 4: Refactor AppNavbar to use notifications store

**Files:**
- Modify: `frontend/src/components/AppNavbar.vue`

The current AppNavbar (292 lines) has inline notification polling in the script section (lines 97, 104, 118-125, 127). We need to replace it with the notifications store.

- [ ] **Step 1: Replace imports**

Find:
```js
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { notificationsAPI } from '@/api'
```

Replace with:
```js
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useNotificationsStore } from '@/stores/notifications'
```

- [ ] **Step 2: Replace unread ref with store**

Find:
```js
const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const showMenu = ref(false)
const menuRef = ref(null)
const unread = ref(0)
const drawerOpen = ref(false)
```

Replace with:
```js
const auth = useAuthStore()
const theme = useThemeStore()
const notifStore = useNotificationsStore()
const route = useRoute()
const showMenu = ref(false)
const menuRef = ref(null)
const drawerOpen = ref(false)
```

- [ ] **Step 3: Replace onMounted polling with store**

Find:
```js
let interval
onMounted(async () => {
  try { unread.value = (await notificationsAPI.unreadCount()).data.count } catch {}
  interval = setInterval(async () => {
    try { unread.value = (await notificationsAPI.unreadCount()).data.count } catch {}
  }, 30000)
  document.addEventListener('click', onClickOut)
})
```

Replace with:
```js
onMounted(() => {
  notifStore.startPolling()
  document.addEventListener('click', onClickOut)
})
```

- [ ] **Step 4: Replace onUnmounted cleanup**

Find:
```js
onUnmounted(() => {
  clearInterval(interval)
  document.removeEventListener('click', onClickOut)
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onEscape)
})
```

Replace with:
```js
onUnmounted(() => {
  notifStore.stopPolling()
  document.removeEventListener('click', onClickOut)
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onEscape)
})
```

- [ ] **Step 5: Update template to use store**

Find:
```html
          <span v-if="unread > 0" class="notif-dot">{{ unread > 9 ? '9+' : unread }}</span>
```

Replace with:
```html
          <span v-if="notifStore.unreadCount > 0" class="notif-dot">{{ notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount }}</span>
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/AppNavbar.vue
git commit -m "refactor: use notifications store in AppNavbar"
```

---

### Task 5: Refactor NotificationsPage to use store + skeleton

**Files:**
- Modify: `frontend/src/views/NotificationsPage.vue`

The current NotificationsPage (104 lines) has all inline state and API calls. We replace them with the notifications store and add skeleton loaders.

- [ ] **Step 1: Replace the entire `<script setup>` block**

Find the current script block (lines 35-71):
```js
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsAPI } from '@/api'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const toast = useToastStore()
const notifs = ref([])
const loading = ref(true)
const unreadOnly = ref(false)
const iconMap = { info: 'info', review: 'star', application: 'send', chat: 'chat', warning: 'warning' }

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

async function fetchNotifs() {
  loading.value = true
  try { notifs.value = (await notificationsAPI.list(unreadOnly.value)).data }
  catch {} finally { loading.value = false }
}

async function markRead(n) {
  if (!n.is_read) { try { await notificationsAPI.markRead(n.id); n.is_read = true } catch {} }
  if (n.link) router.push(n.link)
}

async function markAllRead() {
  try { await notificationsAPI.markAllRead(); notifs.value.forEach(n => n.is_read = true); toast.success('All marked read') } catch {}
}

onMounted(fetchNotifs)
</script>
```

Replace with:
```js
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import { useToastStore } from '@/stores/toast'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const router = useRouter()
const store = useNotificationsStore()
const toast = useToastStore()
const unreadOnly = ref(false)
const iconMap = { info: 'info', review: 'star', application: 'send', chat: 'chat', warning: 'warning' }

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

async function handleFilterChange() {
  await store.fetchList(unreadOnly.value)
}

async function markRead(n) {
  if (!n.is_read) await store.markRead(n.id)
  if (n.link) router.push(n.link)
}

async function markAllRead() {
  await store.markAllRead()
  toast.success('All marked read')
}

onMounted(() => store.fetchList(unreadOnly.value))
</script>
```

- [ ] **Step 2: Update the template**

Find the entire `<template>` block (lines 1-33):
```html
<template>
  <div class="page container">
    <header class="page-header">
      <h1>Notifications</h1>
      <div class="header-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="unreadOnly" @change="fetchNotifs" />
          <span>Unread only</span>
        </label>
        <button class="btn btn-secondary btn-sm" @click="markAllRead" :disabled="!notifs.length">
          <span class="material-icons-round">done_all</span>Mark all read
        </button>
      </div>
    </header>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="notifs.length" class="notifs-list">
      <div v-for="n in notifs" :key="n.id" class="notif-card" :class="{ unread: !n.is_read }" @click="markRead(n)">
        <div class="notif-icon" :class="`notif-${n.notification_type}`">
          <span class="material-icons-round">{{ iconMap[n.notification_type] || 'notifications' }}</span>
        </div>
        <div class="notif-content">
          <div class="notif-title">{{ n.title }}</div>
          <p v-if="n.message" class="notif-message">{{ n.message }}</p>
          <span class="notif-time">{{ timeAgo(n.created_at) }}</span>
        </div>
        <div v-if="!n.is_read" class="notif-dot"></div>
      </div>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">notifications_none</span>
      <h3>{{ unreadOnly ? 'No unread notifications' : 'No notifications yet' }}</h3>
    </div>
  </div>
</template>
```

Replace with:
```html
<template>
  <div class="page container">
    <header class="page-header">
      <h1>Notifications</h1>
      <div class="header-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="unreadOnly" @change="handleFilterChange" />
          <span>Unread only</span>
        </label>
        <button class="btn btn-secondary btn-sm" @click="markAllRead" :disabled="!store.items.length">
          <span class="material-icons-round">done_all</span>Mark all read
        </button>
      </div>
    </header>
    <div v-if="store.loading" class="notifs-list">
      <div v-for="n in 5" :key="n" class="notif-card" style="pointer-events: none;">
        <div class="notif-icon">
          <SkeletonBlock width="36px" height="36px" border-radius="var(--radius-md)" />
        </div>
        <div class="notif-content" style="display: flex; flex-direction: column; gap: 6px;">
          <SkeletonBlock height="14px" width="60%" />
          <SkeletonBlock height="12px" width="80%" />
          <SkeletonBlock height="10px" width="30%" />
        </div>
      </div>
    </div>
    <div v-else-if="store.items.length" class="notifs-list">
      <div v-for="n in store.items" :key="n.id" class="notif-card" :class="{ unread: !n.is_read }" @click="markRead(n)">
        <div class="notif-icon" :class="`notif-${n.notification_type}`">
          <span class="material-icons-round">{{ iconMap[n.notification_type] || 'notifications' }}</span>
        </div>
        <div class="notif-content">
          <div class="notif-title">{{ n.title }}</div>
          <p v-if="n.message" class="notif-message">{{ n.message }}</p>
          <span class="notif-time">{{ timeAgo(n.created_at) }}</span>
        </div>
        <div v-if="!n.is_read" class="notif-dot"></div>
      </div>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">notifications_none</span>
      <h3>{{ unreadOnly ? 'No unread notifications' : 'No notifications yet' }}</h3>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/NotificationsPage.vue
git commit -m "refactor: use notifications store + skeleton in NotificationsPage"
```

---

### Task 6: Refactor ProjectsPage to use store + skeleton

**Files:**
- Modify: `frontend/src/views/ProjectsPage.vue`

The current ProjectsPage (106 lines) has inline projects state, loading, total, and fetchProjects(). We replace the data layer with the projects store while keeping filter UI state local.

- [ ] **Step 1: Replace the entire `<script setup>` block**

Find the current script block (lines 55-88):
```js
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'

const auth = useAuthStore()
const projects = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const size = 12
const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const totalPages = computed(() => Math.ceil(total.value / size))

let timer
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchProjects() }, 300) }

async function fetchProjects() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value !== '') params.is_student_project = typeFilter.value === 'true'
    const { data } = await projectsAPI.list(params)
    projects.value = data.items
    total.value = data.total
  } catch {} finally { loading.value = false }
}

onMounted(fetchProjects)
</script>
```

Replace with:
```js
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const auth = useAuthStore()
const store = useProjectsStore()
const page = ref(1)
const size = 12
const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const totalPages = computed(() => Math.ceil(store.total / size))

let timer
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchProjects() }, 300) }

async function fetchProjects() {
  const params = { page: page.value, size }
  if (search.value) params.search = search.value
  if (statusFilter.value) params.status = statusFilter.value
  if (typeFilter.value !== '') params.is_student_project = typeFilter.value === 'true'
  await store.fetchList(params)
}

onMounted(fetchProjects)
</script>
```

- [ ] **Step 2: Update the template**

Find:
```html
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="projects.length" class="projects-grid">
      <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
    </div>
    <div v-else class="empty-state">
```

Replace with:
```html
    <div v-if="store.loading" class="projects-grid">
      <div v-for="n in 6" :key="n" class="card" style="display: flex; flex-direction: column; gap: 12px;">
        <SkeletonBlock height="20px" width="70%" />
        <SkeletonBlock height="14px" width="40%" />
        <SkeletonBlock height="60px" />
        <div style="display: flex; gap: 6px;">
          <SkeletonBlock height="22px" width="60px" border-radius="var(--radius-full)" />
          <SkeletonBlock height="22px" width="80px" border-radius="var(--radius-full)" />
        </div>
      </div>
    </div>
    <div v-else-if="store.items.length" class="projects-grid">
      <ProjectCard v-for="p in store.items" :key="p.id" :project="p" />
    </div>
    <div v-else class="empty-state">
```

Also update the page sub count. Find:
```html
        <p class="page-sub">{{ total }} projects available</p>
```

Replace with:
```html
        <p class="page-sub">{{ store.total }} projects available</p>
```

Also update the pagination total check. Find:
```html
    <div v-if="totalPages > 1" class="pagination">
```

This stays the same since `totalPages` is a local computed that already references `store.total`.

- [ ] **Step 3: Remove unused CSS**

Find and remove:
```css
.loading-center { display: flex; justify-content: center; padding: 4rem; }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ProjectsPage.vue
git commit -m "refactor: use projects store + skeleton in ProjectsPage"
```

---

### Task 7: Refactor ProjectDetailPage to use projects store + skeleton

**Files:**
- Modify: `frontend/src/views/ProjectDetailPage.vue`

The ProjectDetailPage is large (395 lines). We only change: project fetching, update, delete to go through the store. All other inline state (applications, files, myApp) stays local. We also replace the loading spinner with a skeleton.

- [ ] **Step 1: Update imports**

Find:
```js
import { projectsAPI, applicationsAPI, filesAPI, reviewsAPI, chatAPI } from '@/api'
```

Replace with:
```js
import { useProjectsStore } from '@/stores/projects'
import { applicationsAPI, filesAPI, reviewsAPI, chatAPI } from '@/api'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
```

- [ ] **Step 2: Add store and keep project as local ref synced from store**

Find:
```js
const toast = useToastStore()

const project = ref(null)
```

Replace with:
```js
const toast = useToastStore()
const projectsStore = useProjectsStore()

const project = ref(null)
```

- [ ] **Step 3: Update load() to use store**

Find:
```js
async function load() {
  const id = route.params.id
  try {
    project.value = (await projectsAPI.get(id)).data
```

Replace with:
```js
async function load() {
  const id = route.params.id
  try {
    await projectsStore.fetchOne(id)
    project.value = projectsStore.currentProject
```

- [ ] **Step 4: Update changeStatus to use store**

Find:
```js
async function changeStatus(status) {
  try {
    await projectsAPI.update(project.value.id, { status })
    project.value.status = status
    toast.success('Status updated')
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```

Replace with:
```js
async function changeStatus(status) {
  try {
    await projectsStore.update(project.value.id, { status })
    project.value.status = status
    toast.success('Status updated')
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```

- [ ] **Step 5: Update deleteProject to use store**

Find:
```js
async function deleteProject() {
  showDeleteConfirm.value = false
  try { await projectsAPI.delete(project.value.id); toast.success('Deleted'); router.push('/projects') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```

Replace with:
```js
async function deleteProject() {
  showDeleteConfirm.value = false
  try { await projectsStore.remove(project.value.id); toast.success('Deleted'); router.push('/projects') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```

- [ ] **Step 6: Replace the loading spinner with skeleton**

Find the bottom of the template (the spinner fallback):
```html
  <div v-else class="loading-center"><div class="spinner"></div></div>
</template>
```

Replace with:
```html
  <div v-else class="page container">
    <div class="detail-header">
      <div style="flex: 1; display: flex; flex-direction: column; gap: 10px;">
        <div style="display: flex; gap: 6px;">
          <SkeletonBlock height="24px" width="80px" border-radius="var(--radius-full)" />
        </div>
        <SkeletonBlock height="28px" width="60%" />
        <div style="display: flex; gap: 16px;">
          <SkeletonBlock height="14px" width="100px" />
          <SkeletonBlock height="14px" width="80px" />
          <SkeletonBlock height="14px" width="120px" />
        </div>
      </div>
    </div>
    <div class="detail-section">
      <SkeletonBlock height="20px" width="120px" />
      <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
        <SkeletonBlock height="14px" />
        <SkeletonBlock height="14px" />
        <SkeletonBlock height="14px" width="70%" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/ProjectDetailPage.vue
git commit -m "refactor: use projects store + skeleton in ProjectDetailPage"
```

---

### Task 8: Refactor CreateProjectPage to use projects store

**Files:**
- Modify: `frontend/src/views/CreateProjectPage.vue`

Small change — only the create call goes through the store.

- [ ] **Step 1: Update imports**

Find:
```js
import { projectsAPI, skillsAPI } from '@/api'
```

Replace with:
```js
import { useProjectsStore } from '@/stores/projects'
import { skillsAPI } from '@/api'
```

- [ ] **Step 2: Add store const**

Find:
```js
const toast = useToastStore()
const loading = ref(false)
```

Replace with:
```js
const toast = useToastStore()
const projectsStore = useProjectsStore()
const loading = ref(false)
```

- [ ] **Step 3: Update submit to use store**

Find:
```js
    const { data } = await projectsAPI.create(payload)
    toast.success('Project created!')
    router.push(`/projects/${data.id}`)
```

Replace with:
```js
    const data = await projectsStore.create(payload)
    toast.success('Project created!')
    router.push(`/projects/${data.id}`)
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/CreateProjectPage.vue
git commit -m "refactor: use projects store for create in CreateProjectPage"
```

---

### Task 9: Add skeleton to DashboardPage

**Files:**
- Modify: `frontend/src/views/DashboardPage.vue`

DashboardPage keeps its own `projectsAPI.list({ size: 4 })` call (different query shape than the store's browse list). We just add a loading state and skeleton.

- [ ] **Step 1: Update imports and add loading ref**

Find:
```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, adminAPI, applicationsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'

const auth = useAuthStore()
const projects = ref([])
```

Replace with:
```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, adminAPI, applicationsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const auth = useAuthStore()
const projects = ref([])
const projectsLoading = ref(true)
```

- [ ] **Step 2: Update onMounted to track loading**

Find:
```js
onMounted(async () => {
  try { projects.value = (await projectsAPI.list({ page: 1, size: 4 })).data.items } catch {}
  if (auth.isAdmin) { try { stats.value = (await adminAPI.stats()).data } catch {} }
  if (auth.isStudent) { try { myApps.value = (await applicationsAPI.my()).data.length } catch {} }
})
```

Replace with:
```js
onMounted(async () => {
  try { projects.value = (await projectsAPI.list({ page: 1, size: 4 })).data.items } catch {}
  finally { projectsLoading.value = false }
  if (auth.isAdmin) { try { stats.value = (await adminAPI.stats()).data } catch {} }
  if (auth.isStudent) { try { myApps.value = (await applicationsAPI.my()).data.length } catch {} }
})
```

- [ ] **Step 3: Update the recent projects section in the template**

Find:
```html
      <div v-if="projects.length" class="grid-2">
        <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
      </div>
      <div v-else class="empty-state">
        <span class="material-icons-round">folder_open</span>
        <h3>No projects yet</h3>
      </div>
```

Replace with:
```html
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
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/DashboardPage.vue
git commit -m "feat: add skeleton loader to DashboardPage"
```

---

### Task 10: Build verification

**Files:**
- None (verification only)

- [ ] **Step 1: Install dependencies if needed**

```bash
cd frontend && npm install
```

- [ ] **Step 2: Run production build**

```bash
cd frontend && npx vite build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit (only if build required fixes)**

Only commit if you had to fix anything. If build passes clean, skip this step.
