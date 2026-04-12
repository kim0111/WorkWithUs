# Frontend Phase 2A: Navigation, Guards & Error Pages

## Overview

Add foundational frontend infrastructure: a 404 catch-all page, role-based route guards, and a mobile slide-out navigation drawer. These are prerequisites for all subsequent Phase 2 work.

**Scope:** 1 new view, 2 modified files (router, navbar), minor CSS additions.

## 1. 404 Not Found Page

### File
- Create: `frontend/src/views/NotFoundPage.vue`

### Design
Minimal page matching the existing design system:
- Large "404" heading (`font-size: 4rem`, `font-weight: 700`, `color: var(--gray-300)`)
- Subtitle: "This page doesn't exist" (`color: var(--gray-500)`)
- "Back to home" button using `router-link` to `/` with class `btn btn-primary`
- Centered vertically and horizontally using flexbox
- No navbar shown (same as login/register — excluded via `showNav` computed in App.vue)

### Route
Add catch-all route at the **end** of the routes array in `router/index.js`:
```js
{ path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFoundPage.vue') }
```

### App.vue Change
Add `'NotFound'` to the list of routes where `showNav` is false, so the 404 page renders full-screen without the navbar.

## 2. Role-Based Route Guards

### Route Meta Changes
Add `roles` array to routes that need role restriction:

| Route | Current meta | New meta |
|-------|-------------|----------|
| `/projects/create` | `{ auth: true }` | `{ auth: true, roles: ['company', 'admin'] }` |
| `/my-applications` | `{ auth: true }` | `{ auth: true, roles: ['student'] }` |
| `/admin` | `{ auth: true, admin: true }` | No change (already works) |

### Guard Logic
Add one check to the existing `router.beforeEach` in `router/index.js`, **after** the auth check:

```js
if (to.meta.roles && !to.meta.roles.includes(auth.user?.role)) return '/dashboard'
```

Order of checks:
1. If `meta.auth` and not authenticated → redirect to `/login`
2. If `meta.guest` and authenticated → redirect to `/dashboard`
3. If `meta.admin` and not admin → redirect to `/dashboard`
4. **NEW:** If `meta.roles` and user role not in list → redirect to `/dashboard`

Silent redirect — no error message. The navbar already hides links by role, so this is a safety net for direct URL access only.

## 3. Mobile Slide-Out Drawer

### File
- Modify: `frontend/src/components/AppNavbar.vue`

### New State
```js
const drawerOpen = ref(false)
```

### Template Additions

**Hamburger button** — added to `.navbar-inner`, between brand and `.nav-right`:
```html
<button class="hamburger-btn" @click="drawerOpen = !drawerOpen">
  <span class="material-icons-round">menu</span>
</button>
```
Visible only on screens ≤768px via media query (same breakpoint that hides `.nav-links`).

**Drawer + backdrop** — added after `</nav>`, wrapped in a `<Teleport to="body">`:
```html
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
          <!-- Same nav links as desktop, each @click="drawerOpen = false" -->
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
```

### Drawer Behavior
- Backdrop click closes drawer
- Any link click closes drawer
- Body scroll locked when open: `watch(drawerOpen, (open) => { document.body.style.overflow = open ? 'hidden' : '' })`
- Cleanup in `onUnmounted`: restore body overflow

### CSS

**Hamburger button** (hidden on desktop):
```css
.hamburger-btn {
  display: none; /* shown via media query */
  align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: var(--radius-md);
  background: none; border: none; color: var(--gray-500); cursor: pointer;
}
.hamburger-btn:hover { background: var(--gray-100); color: var(--gray-700); }
```

**Drawer styles:**
```css
.drawer-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200;
}
.drawer-panel {
  position: fixed; top: 0; left: 0; bottom: 0; width: 280px;
  background: var(--white); display: flex; flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; border-bottom: 1px solid var(--gray-200);
}
.drawer-close {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: var(--radius-md);
  background: none; border: none; color: var(--gray-500); cursor: pointer;
}
.drawer-close:hover { background: var(--gray-100); }
.drawer-links {
  flex: 1; padding: 8px; display: flex; flex-direction: column; gap: 2px;
}
.drawer-link {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px;
  border-radius: var(--radius-md); color: var(--gray-700); font-size: 0.875rem;
  font-weight: 500; text-decoration: none; background: none; border: none;
  width: 100%; cursor: pointer; font-family: var(--font); transition: all 0.15s ease;
}
.drawer-link:hover { background: var(--gray-100); }
.drawer-link.router-link-active { color: var(--accent-text); background: var(--accent-light); }
.drawer-link.danger { color: var(--danger); }
.drawer-link .material-icons-round { font-size: 20px; color: var(--gray-400); }
.drawer-link.danger .material-icons-round { color: var(--danger); }
.drawer-footer {
  padding: 8px; border-top: 1px solid var(--gray-200);
  display: flex; flex-direction: column; gap: 2px;
}
```

**Transitions:**
```css
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer-panel, .drawer-leave-active .drawer-panel {
  transition: transform 0.2s ease;
}
.drawer-enter-from .drawer-panel, .drawer-leave-to .drawer-panel {
  transform: translateX(-100%);
}
```

**Media query additions** (extend existing `@media (max-width: 768px)` block):
```css
@media (max-width: 768px) {
  .nav-links { display: none; }
  .hamburger-btn { display: flex; }
}
```

### Route watcher
Close drawer on route change (handles edge cases like back/forward navigation):
```js
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
watch(() => route.path, () => { drawerOpen.value = false })
```

## Files Summary

| Action | File | Changes |
|--------|------|---------|
| Create | `src/views/NotFoundPage.vue` | New 404 page |
| Modify | `src/router/index.js` | Catch-all route, `roles` meta, guard check |
| Modify | `src/components/AppNavbar.vue` | Hamburger + drawer |
| Modify | `src/App.vue` | Add NotFound to `showNav` exclusion list |
