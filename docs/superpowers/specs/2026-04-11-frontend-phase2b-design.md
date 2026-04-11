# Frontend Phase 2B: Pinia Data Stores & Skeleton Loaders

## Overview

Centralize project and notification data into Pinia stores, replace spinner-based loading states with skeleton loaders, and refactor views to consume store data instead of making inline API calls.

**Scope:** 1 new component, 2 new stores, 4 modified views, 1 modified component.

## 1. SkeletonBlock Component

### File
- Create: `frontend/src/components/SkeletonBlock.vue`

### Design
A single reusable animated placeholder element:
- Props: `width` (String, default `'100%'`), `height` (String, default `'16px'`), `borderRadius` (String, default `'var(--radius-md)'`)
- Renders a `<div>` with inline styles for width, height, border-radius
- CSS shimmer animation: a light gradient (`var(--gray-200)` to `var(--gray-100)` to `var(--gray-200)`) sweeps left-to-right on a 1.5s infinite loop
- Background color: `var(--gray-200)` base

### Usage Pattern
Views compose skeleton layouts inline:
```html
<div v-if="loading" class="projects-grid">
  <div v-for="n in 6" :key="n" class="card" style="padding: 20px;">
    <SkeletonBlock height="20px" width="70%" />
    <SkeletonBlock height="14px" width="40%" />
    <SkeletonBlock height="60px" />
  </div>
</div>
<div v-else> ... real content ... </div>
```

No separate skeleton card components — each view composes its own skeleton from SkeletonBlock, keeping the component count low and avoiding drift.

## 2. Notifications Store

### File
- Create: `frontend/src/stores/notifications.js`

### State
```js
const items = ref([])          // current page of notifications
const unreadCount = ref(0)     // badge count
const loading = ref(false)     // for list fetching
const unreadOnly = ref(false)  // filter toggle
```

### Actions
```js
async function fetchUnreadCount()
  // calls notificationsAPI.unreadCount()
  // updates unreadCount

async function fetchList(unreadFilter = false, page = 1)
  // sets loading = true
  // calls notificationsAPI.list(unreadFilter, page)
  // updates items
  // sets loading = false

async function markRead(id)
  // calls notificationsAPI.markRead(id)
  // updates the item in items array (set is_read = true)
  // decrements unreadCount

async function markAllRead()
  // calls notificationsAPI.markAllRead()
  // sets unreadCount = 0
  // updates all items in array to is_read = true

let pollInterval = null
function startPolling()
  // if pollInterval already set, return (prevent duplicates)
  // call fetchUnreadCount() immediately
  // set pollInterval = setInterval(fetchUnreadCount, 30000)

function stopPolling()
  // clearInterval(pollInterval)
  // pollInterval = null
```

### Consumers

**AppNavbar** (modify `frontend/src/components/AppNavbar.vue`):
- Remove: `unread` ref, `notificationsAPI` import, inline polling in `onMounted`, `clearInterval` in `onUnmounted`
- Add: `import { useNotificationsStore }`, `const notifStore = useNotificationsStore()`
- `onMounted`: call `notifStore.startPolling()` (replaces inline poll)
- `onUnmounted`: call `notifStore.stopPolling()` (replaces clearInterval)
- Template: replace `unread` with `notifStore.unreadCount`

**NotificationsPage** (modify `frontend/src/views/NotificationsPage.vue`):
- Remove: `notifs` ref, `loading` ref, `unreadOnly` ref, `fetchNotifs()`, `markRead()`, `markAllRead()`, `notificationsAPI` import
- Add: `import { useNotificationsStore }`, `const store = useNotificationsStore()`
- `onMounted`: call `store.fetchList()`
- Template: replace `notifs` with `store.items`, `loading` with `store.loading`, `unreadOnly` with `store.unreadOnly`
- `markRead(n)`: call `store.markRead(n.id)`, then navigate if `n.link`
- `markAllRead`: call `store.markAllRead()`
- Filter toggle: `store.unreadOnly = !store.unreadOnly; store.fetchList(store.unreadOnly)`
- Add skeleton: replace spinner with 5 skeleton rows while `store.loading`

### Skeleton Layout for NotificationsPage
```html
<div v-if="store.loading" class="notifs-list">
  <div v-for="n in 5" :key="n" class="notif-card" style="pointer-events: none;">
    <div class="notif-icon"><SkeletonBlock width="36px" height="36px" border-radius="var(--radius-md)" /></div>
    <div class="notif-content" style="display: flex; flex-direction: column; gap: 6px;">
      <SkeletonBlock height="14px" width="60%" />
      <SkeletonBlock height="12px" width="80%" />
      <SkeletonBlock height="10px" width="30%" />
    </div>
  </div>
</div>
```

## 3. Projects Store

### File
- Create: `frontend/src/stores/projects.js`

### State
```js
const items = ref([])           // paginated browse list
const total = ref(0)            // total count from API
const currentProject = ref(null) // single project detail
const loading = ref(false)      // for list fetching
const detailLoading = ref(false) // for single project fetching
```

### Actions
```js
async function fetchList(params = {})
  // sets loading = true
  // calls projectsAPI.list(params)
  // updates items = data.items, total = data.total
  // sets loading = false

async function fetchOne(id)
  // sets detailLoading = true
  // calls projectsAPI.get(id)
  // updates currentProject = data
  // sets detailLoading = false

async function create(data)
  // calls projectsAPI.create(data)
  // returns response data (caller navigates to project)

async function update(id, data)
  // calls projectsAPI.update(id, data)
  // if currentProject.id === id, update currentProject

async function remove(id)
  // calls projectsAPI.delete(id)
  // clears currentProject if it matches
```

### Consumers

**ProjectsPage** (modify `frontend/src/views/ProjectsPage.vue`):
- Remove: `projects` ref, `loading` ref, `total` ref, `projectsAPI` import, `fetchProjects()` function
- Add: `import { useProjectsStore }`, `const store = useProjectsStore()`
- Keep: `page`, `search`, `statusFilter`, `typeFilter` refs locally (these are UI state, not shared data)
- `fetchProjects()` becomes a local function that builds params and calls `store.fetchList(params)`
- Template: replace `projects` with `store.items`, `loading` with `store.loading`, `total` with `store.total`
- `totalPages` computed: `Math.ceil(store.total / size)`
- Add skeleton: replace spinner with 6 skeleton cards while `store.loading`

**ProjectDetailPage** (modify `frontend/src/views/ProjectDetailPage.vue`):
- Replace: `project` ref → `store.currentProject`
- Replace: `projectsAPI.get(id)` call in `load()` → `await store.fetchOne(id)`; then `project.value = store.currentProject`
- Keep: all other inline state (applications, files, myApp) — these are page-specific, not shared
- Replace: `projectsAPI.update()` → `store.update()`
- Replace: `projectsAPI.delete()` → `store.remove()`
- Add skeleton: replace the bottom spinner (`<div v-else class="loading-center">`) with skeleton blocks for the header area while `!project`

**DashboardPage** (modify `frontend/src/views/DashboardPage.vue`):
- Replace: `projects` ref and `projectsAPI.list({ page: 1, size: 4 })` → use `store.fetchList()` result
- Note: DashboardPage needs the 4 most recent projects but shouldn't overwrite the browse list. Solution: call `projectsAPI.list({ page: 1, size: 4 })` directly (keep the inline call) since the dashboard's "recent 4" is a different query than the paginated browse. Don't force this through the store.
- Keep: `projectsAPI` import for the dashboard's `size: 4` query
- Add skeleton: replace the projects section with 4 skeleton cards while loading

**CreateProjectPage** (modify `frontend/src/views/CreateProjectPage.vue`):
- Replace: `projectsAPI.create(payload)` → `store.create(payload)`
- Rest stays the same

## 4. Skeleton Integration Summary

| View | Skeleton Layout | Replaces |
|------|----------------|----------|
| ProjectsPage | Grid of 6 cards, each with 3 SkeletonBlocks | `<div class="loading-center"><div class="spinner">` |
| ProjectDetailPage | Header area with badge, title, meta placeholders | `<div v-else class="loading-center"><div class="spinner">` |
| NotificationsPage | 5 notification card rows with icon + text blocks | `<div v-if="loading" class="loading-center"><div class="spinner">` |
| DashboardPage | 4 project cards in the "Recent Projects" section | No loading state currently (just empty) |

## Files Summary

| Action | File | Changes |
|--------|------|---------|
| Create | `src/components/SkeletonBlock.vue` | New skeleton component |
| Create | `src/stores/notifications.js` | New notifications store |
| Create | `src/stores/projects.js` | New projects store |
| Modify | `src/components/AppNavbar.vue` | Use notifications store instead of inline polling |
| Modify | `src/views/NotificationsPage.vue` | Use notifications store + skeleton |
| Modify | `src/views/ProjectsPage.vue` | Use projects store + skeleton |
| Modify | `src/views/ProjectDetailPage.vue` | Use projects store + skeleton |
| Modify | `src/views/CreateProjectPage.vue` | Use projects store for create |
| Modify | `src/views/DashboardPage.vue` | Add skeleton for recent projects |
