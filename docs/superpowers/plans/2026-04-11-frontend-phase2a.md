# Frontend Phase 2A: Navigation, Guards & Error Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 404 catch-all page, role-based route guards, and a mobile slide-out navigation drawer as foundational infrastructure for Phase 2.

**Architecture:** One new view (NotFoundPage), modifications to the router (catch-all route + role guard), AppNavbar (hamburger + drawer), and App.vue (showNav exclusion). All changes are frontend-only — no backend or API changes.

**Tech Stack:** Vue 3 Composition API, Vue Router 4, CSS variables from existing design system, Material Icons

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/views/NotFoundPage.vue` | 404 error page — centered layout with heading, subtitle, home link |
| Modify | `frontend/src/router/index.js` | Catch-all route, `roles` meta on 2 routes, role guard in `beforeEach` |
| Modify | `frontend/src/App.vue` | Add `'NotFound'` to `showNav` exclusion list |
| Modify | `frontend/src/components/AppNavbar.vue` | Hamburger button, slide-out drawer, body scroll lock, route watcher |

---

### Task 1: Create NotFoundPage.vue

**Files:**
- Create: `frontend/src/views/NotFoundPage.vue`

- [ ] **Step 1: Create the 404 page component**

Create `frontend/src/views/NotFoundPage.vue`:

```vue
<template>
  <div class="not-found">
    <h1 class="not-found-code">404</h1>
    <p class="not-found-message">This page doesn't exist</p>
    <router-link to="/" class="btn btn-primary">Back to home</router-link>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 12px;
  text-align: center;
  padding: 24px;
}
.not-found-code {
  font-size: 4rem;
  font-weight: 700;
  color: var(--gray-300);
  line-height: 1;
}
.not-found-message {
  color: var(--gray-500);
  font-size: 1rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/NotFoundPage.vue
git commit -m "feat: add 404 NotFoundPage view"
```

---

### Task 2: Add catch-all route and role-based guards to router

**Files:**
- Modify: `frontend/src/router/index.js`

The current file looks like this:

```js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginPage.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterPage.vue'), meta: { guest: true } },
  { path: '/verify-email', name: 'VerifyEmail', component: () => import('@/views/VerifyEmailPage.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/DashboardPage.vue'), meta: { auth: true } },
  { path: '/projects', name: 'Projects', component: () => import('@/views/ProjectsPage.vue') },
  { path: '/projects/create', name: 'CreateProject', component: () => import('@/views/CreateProjectPage.vue'), meta: { auth: true } },
  { path: '/projects/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetailPage.vue') },
  { path: '/profile/:id', name: 'Profile', component: () => import('@/views/ProfilePage.vue') },
  { path: '/my-applications', name: 'MyApps', component: () => import('@/views/MyApplicationsPage.vue'), meta: { auth: true } },
  { path: '/chat', name: 'ChatList', component: () => import('@/views/ChatListPage.vue'), meta: { auth: true } },
  { path: '/chat/:roomId', name: 'ChatRoom', component: () => import('@/views/ChatRoomPage.vue'), meta: { auth: true } },
  { path: '/notifications', name: 'Notifications', component: () => import('@/views/NotificationsPage.vue'), meta: { auth: true } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminPage.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: () => ({ top: 0 }) })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user && localStorage.getItem('access_token')) await auth.fetchUser()
  if (to.meta.auth && !auth.isAuth) return '/login'
  if (to.meta.guest && auth.isAuth) return '/dashboard'
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
})

export default router
```

- [ ] **Step 1: Add `roles` meta to `/projects/create` route**

Find this line:
```js
  { path: '/projects/create', name: 'CreateProject', component: () => import('@/views/CreateProjectPage.vue'), meta: { auth: true } },
```

Replace with:
```js
  { path: '/projects/create', name: 'CreateProject', component: () => import('@/views/CreateProjectPage.vue'), meta: { auth: true, roles: ['company', 'admin'] } },
```

- [ ] **Step 2: Add `roles` meta to `/my-applications` route**

Find this line:
```js
  { path: '/my-applications', name: 'MyApps', component: () => import('@/views/MyApplicationsPage.vue'), meta: { auth: true } },
```

Replace with:
```js
  { path: '/my-applications', name: 'MyApps', component: () => import('@/views/MyApplicationsPage.vue'), meta: { auth: true, roles: ['student'] } },
```

- [ ] **Step 3: Add catch-all 404 route at end of routes array**

Find this line (the last route in the array):
```js
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminPage.vue'), meta: { auth: true, admin: true } },
]
```

Replace with:
```js
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminPage.vue'), meta: { auth: true, admin: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFoundPage.vue') },
]
```

- [ ] **Step 4: Add role guard to `beforeEach`**

Find this block:
```js
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user && localStorage.getItem('access_token')) await auth.fetchUser()
  if (to.meta.auth && !auth.isAuth) return '/login'
  if (to.meta.guest && auth.isAuth) return '/dashboard'
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
})
```

Replace with:
```js
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user && localStorage.getItem('access_token')) await auth.fetchUser()
  if (to.meta.auth && !auth.isAuth) return '/login'
  if (to.meta.guest && auth.isAuth) return '/dashboard'
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
  if (to.meta.roles && !to.meta.roles.includes(auth.user?.role)) return '/dashboard'
})
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: add catch-all 404 route and role-based route guards"
```

---

### Task 3: Update App.vue to hide navbar on 404 page

**Files:**
- Modify: `frontend/src/App.vue`

The current `showNav` computed is on line 22:

```js
const showNav = computed(() => !['Login','Register','Home'].includes(route.name))
```

- [ ] **Step 1: Add 'NotFound' to the exclusion list**

Find:
```js
const showNav = computed(() => !['Login','Register','Home'].includes(route.name))
```

Replace with:
```js
const showNav = computed(() => !['Login','Register','Home','NotFound'].includes(route.name))
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: hide navbar on 404 page"
```

---

### Task 4: Add mobile hamburger button and slide-out drawer to AppNavbar

**Files:**
- Modify: `frontend/src/components/AppNavbar.vue`

This is the largest task. The current AppNavbar has 136 lines. We need to add: a `drawerOpen` ref, a hamburger button in the template, a Teleport'd drawer with backdrop, body scroll lock via watcher, route watcher to close drawer, and all the CSS.

The current template structure:
```
<nav class="navbar">
  <div class="navbar-inner container">
    <router-link to="/dashboard" class="nav-brand">...</router-link>
    <div class="nav-links">...</div>
    <div class="nav-right">...</div>
  </div>
</nav>
```

The current script imports:
```js
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { notificationsAPI } from '@/api'
```

- [ ] **Step 1: Update script imports and add new state**

Find:
```js
import { ref, onMounted, onUnmounted } from 'vue'
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
import { notificationsAPI } from '@/api'
```

- [ ] **Step 2: Add drawer state, route watcher, and scroll lock**

Find:
```js
const auth = useAuthStore()
const theme = useThemeStore()
const showMenu = ref(false)
const menuRef = ref(null)
const unread = ref(0)
```

Replace with:
```js
const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const showMenu = ref(false)
const menuRef = ref(null)
const unread = ref(0)
const drawerOpen = ref(false)

watch(() => route.path, () => { drawerOpen.value = false })
watch(drawerOpen, (open) => { document.body.style.overflow = open ? 'hidden' : '' })
```

- [ ] **Step 3: Add cleanup for body overflow in onUnmounted**

Find:
```js
onUnmounted(() => {
  clearInterval(interval)
  document.removeEventListener('click', onClickOut)
})
```

Replace with:
```js
onUnmounted(() => {
  clearInterval(interval)
  document.removeEventListener('click', onClickOut)
  document.body.style.overflow = ''
})
```

- [ ] **Step 4: Add hamburger button to template**

Find this in the template (the closing `</router-link>` of the brand, followed by the nav-links div):
```html
      <div class="nav-links">
```

Replace with:
```html
      <button class="hamburger-btn" @click="drawerOpen = !drawerOpen">
        <span class="material-icons-round">menu</span>
      </button>

      <div class="nav-links">
```

- [ ] **Step 5: Add drawer Teleport after closing `</nav>` tag**

Find the closing nav tag:
```html
  </nav>
</template>
```

Replace with:
```html
  </nav>

  <Teleport to="body">
    <transition name="drawer">
      <div v-if="drawerOpen" class="drawer-backdrop" @click="drawerOpen = false">
        <div class="drawer-panel" @click.stop>
          <div class="drawer-header">
            <div class="nav-brand">
              <div class="brand-mark">N</div>
              <span class="brand-text">NexusHub</span>
            </div>
            <button class="drawer-close" @click="drawerOpen = false">
              <span class="material-icons-round">close</span>
            </button>
          </div>
          <div class="drawer-links">
            <router-link to="/projects" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">work_outline</span>Projects
            </router-link>
            <router-link v-if="auth.isStudent" to="/my-applications" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">description</span>Applications
            </router-link>
            <router-link v-if="auth.isCompany || auth.isAdmin || auth.isStudent" to="/projects/create" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">add_circle_outline</span>New Project
            </router-link>
            <router-link v-if="auth.isAuth" to="/chat" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">chat_bubble_outline</span>Chat
            </router-link>
            <router-link v-if="auth.isAdmin" to="/admin" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">admin_panel_settings</span>Admin
            </router-link>
          </div>
          <div class="drawer-footer">
            <router-link :to="`/profile/${auth.user?.id}`" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">person</span>Profile
            </router-link>
            <button class="drawer-link danger" @click="drawerOpen = false; handleLogout()">
              <span class="material-icons-round">logout</span>Sign Out
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>
```

- [ ] **Step 6: Add all new CSS**

Find the existing media query at the end of the `<style scoped>` block:
```css
@media (max-width: 768px) { .nav-links { display: none; } }
</style>
```

Replace with:
```css
.hamburger-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--gray-500);
  cursor: pointer;
}
.hamburger-btn:hover { background: var(--gray-100); color: var(--gray-700); }
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
}
.drawer-panel {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--white);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--gray-200);
}
.drawer-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--gray-500);
  cursor: pointer;
}
.drawer-close:hover { background: var(--gray-100); }
.drawer-links {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.drawer-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--gray-700);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
  font-family: var(--font);
  transition: all 0.15s ease;
}
.drawer-link:hover { background: var(--gray-100); }
.drawer-link.router-link-active { color: var(--accent-text); background: var(--accent-light); }
.drawer-link.danger { color: var(--danger); }
.drawer-link .material-icons-round { font-size: 20px; color: var(--gray-400); }
.drawer-link.danger .material-icons-round { color: var(--danger); }
.drawer-footer {
  padding: 8px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer-panel, .drawer-leave-active .drawer-panel { transition: transform 0.2s ease; }
.drawer-enter-from .drawer-panel, .drawer-leave-to .drawer-panel { transform: translateX(-100%); }
@media (max-width: 768px) {
  .nav-links { display: none; }
  .hamburger-btn { display: flex; }
}
</style>
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/AppNavbar.vue
git commit -m "feat: add mobile hamburger menu with slide-out drawer"
```

---

### Task 5: Build verification

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

Expected: Build succeeds with no errors. Warnings about source maps or chunk sizes are acceptable.

- [ ] **Step 3: Commit (only if build required fixes)**

Only commit if you had to fix anything. If build passes clean, skip this step.
