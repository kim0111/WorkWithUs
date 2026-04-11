# Frontend Phase 2C: Role-Based Dashboard

## Overview

Replace the generic DashboardPage with role-specific content for students, companies, and admins. Each role sees stats, actions, and data sections relevant to their workflow.

**Scope:** 1 modified view (DashboardPage orchestrator), 2 new section components, no new stores or API endpoints.

## 1. DashboardPage Orchestrator

### File
- Modify: `frontend/src/views/DashboardPage.vue`

### Design
The shared header stays (greeting + role badge). Everything below the header is replaced with role-conditional rendering:

```html
<DashboardStudentSection v-if="auth.isStudent" />
<DashboardCompanySection v-else-if="auth.isCompany" />
<!-- Admin section stays inline (already exists, just stat cards + quick actions) -->
<template v-else-if="auth.isAdmin"> ... admin stats + quick actions ... </template>
```

The current Quick Actions grid is kept for admin only (it's already role-gated with v-if). Student and company get their own action links within their sections.

The current "Recent Projects" section is removed from the orchestrator — students get "Suggested Projects" in their section, companies get "My Projects" in theirs, admin keeps the generic recent projects inline.

### Data fetching changes
- Remove: `projectsAPI.list({ page: 1, size: 4 })` call (moved into sections)
- Remove: `applicationsAPI.my()` call (moved into student section)
- Keep: `adminAPI.stats()` call for admin only
- Remove: `projectsLoading`, `projects`, `myApps` refs (moved into sections)
- Keep: `stats` ref for admin

## 2. DashboardStudentSection

### File
- Create: `frontend/src/components/dashboard/DashboardStudentSection.vue`

### Data (fetched on mount)
```js
const apps = ref([])           // from applicationsAPI.my(), sliced to 5
const projectTitles = ref({})  // { projectId: title } resolved in parallel
const rating = ref(null)       // from reviewsAPI.rating(userId)
const suggestedProjects = ref([]) // from projectsAPI.list({ status: 'open', size: 4 })
const loading = ref(true)
```

### onMounted flow
1. Fetch `applicationsAPI.my()` → take first 5, store in `apps`
2. In parallel: resolve project titles for those 5 apps via `projectsAPI.get(pid)` for each unique `project_id`
3. Fetch `reviewsAPI.rating(auth.user.id)` → store in `rating`
4. Fetch `projectsAPI.list({ page: 1, size: 4, status: 'open' })` → store in `suggestedProjects`
5. Set `loading = false`

### Template layout

**Stats row** (3 cards):
| Stat | Value | Source |
|------|-------|--------|
| Active Applications | count of apps with status in [pending, accepted, in_progress, submitted, revision_requested] | `apps` filtered |
| Completed Projects | count of apps with status === 'completed' | `apps` filtered |
| Average Rating | `rating.average_rating` with star icon, or "No reviews" | `rating` |

**My Applications** section (up to 5 recent):
- Section header: "My Applications" with "View All →" link to `/my-applications`
- Each row: project title (resolved), StatusBadge for app status, time ago
- Row is a `router-link` to `/projects/${app.project_id}`
- Loading: 5 skeleton rows
- Empty: "No applications yet" with link to browse projects

**Suggested Projects** section:
- Section header: "Open Projects" with "Browse All →" link to `/projects`
- Uses existing `ProjectCard` component in a `.grid-2`
- Loading: 4 skeleton cards (same pattern as DashboardPage had)
- Empty: "No open projects right now"

### Quick actions (integrated into the layout, not a separate grid):
Students get contextual links embedded in the empty/header states rather than a separate quick actions grid. The "Browse Projects" and "My Applications" links serve this purpose.

## 3. DashboardCompanySection

### File
- Create: `frontend/src/components/dashboard/DashboardCompanySection.vue`

### Data (fetched on mount)
```js
const myProjects = ref([])        // items array from projectsAPI.list({ owner_id: userId, size: 5 })
const myProjectsTotal = ref(0)    // total count from same response
const pendingApps = ref([])       // aggregated from applicationsAPI.byProject() for each project
const totalPending = ref(0)       // full count before slicing to 5
const loading = ref(true)
```

### onMounted flow
1. Fetch `projectsAPI.list({ owner_id: auth.user.id, page: 1, size: 5 })` → store in `myProjects`, build `projectTitles` map
2. For each project in `myProjects`, fetch `applicationsAPI.byProject(pid)` in parallel
3. Aggregate all applications, filter to status === 'pending', sort by `created_at` desc, take first 5 → store in `pendingApps`
4. Set `loading = false`

### Template layout

**Stats row** (3 cards):
| Stat | Value | Source |
|------|-------|--------|
| My Projects | `myProjectsTotal` | API response `total` field |
| Open Positions | count of `myProjects` with status === 'open' | `myProjects` filtered |
| Pending Applications | `totalPending` | full count before slicing to 5 |

**My Projects** section (up to 5):
- Section header: "My Projects" with "New Project →" link to `/projects/create`
- Each row: project title, StatusBadge for project status, application count, created date
- Row is a `router-link` to `/projects/${project.id}`
- Loading: 5 skeleton rows
- Empty: "No projects yet" with link to create one

**Pending Applications** section (up to 5):
- Section header: "Pending Applications" with count badge
- Each row: "User #N applied to {project title}", time ago, "Review" link to `/projects/${pid}`
- Loading: 5 skeleton rows
- Empty: "No pending applications"

### Quick actions:
Companies get a "New Project" link in the My Projects section header, replacing the separate quick actions grid.

## 4. Admin Section (stays inline)

The admin section stays in DashboardPage.vue directly. Changes:
- Keep: stats row (Users, Projects, Applications, Chat Messages)
- Keep: quick actions grid (currently: New Project, Browse Projects, Messages, Profile)
- Keep: "Recent Projects" section with ProjectCard grid + skeleton
- The admin data fetching (`adminAPI.stats()`, `projectsAPI.list()`) stays in DashboardPage

## 5. Shared Patterns

**Skeleton loading:** Both sections use SkeletonBlock for their list rows while loading. Pattern:
```html
<div v-if="loading" class="dash-list">
  <div v-for="n in 5" :key="n" class="dash-list-item" style="pointer-events: none;">
    <SkeletonBlock height="14px" width="50%" />
    <SkeletonBlock height="22px" width="70px" border-radius="var(--radius-full)" />
  </div>
</div>
```

**List item styling:** Both sections use a shared `.dash-list` / `.dash-list-item` pattern — horizontal row with content left, badge/meta right. Each section defines its own scoped styles following this pattern.

**Time ago helper:** Both sections need `timeAgo(date)`. Rather than duplicating, extract to a small utility or just duplicate inline (it's 4 lines). Keep it simple — duplicate is fine for 2 components.

## Files Summary

| Action | File | Changes |
|--------|------|---------|
| Modify | `src/views/DashboardPage.vue` | Thin orchestrator, role-conditional rendering |
| Create | `src/components/dashboard/DashboardStudentSection.vue` | Student stats, applications, suggested projects |
| Create | `src/components/dashboard/DashboardCompanySection.vue` | Company stats, projects, pending applications |
