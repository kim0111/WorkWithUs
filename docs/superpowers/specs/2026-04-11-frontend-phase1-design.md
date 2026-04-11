# Frontend Phase 1: Component Library + Profile Enhancements — Design Spec

## Goal

Build a reusable Vue 3 component library and redesign the profile system so company and student users each get a role-appropriate experience. Companies see their projects and application pipeline; students see education, skills management, and a richer portfolio.

## Scope

- 7 reusable components
- Company profile redesign (new tabs, company info grid, edit modal)
- Student profile redesign (education grid, inline skills, richer portfolio cards)
- Refactor existing code to use new components (ConfirmDialog replaces `confirm()`)
- Design refresh: consistent spacing, better dark mode, polished modals
- New API calls wired up (company-profile, student-profile endpoints already exist in backend)

## Not in Scope

- Pinia data stores for projects/applications/notifications
- 404 route, role-based route guards
- Loading skeletons (beyond what exists)
- Mobile hamburger menu
- Toast system overhaul
- Form validation composable (beyond FormField error display)

---

## Section 1: Reusable Component Library

All components go in `frontend/src/components/`. Each uses `<script setup>`, scoped styles, and the existing CSS variable system from `src/assets/styles.css`.

### 1.1 BaseModal.vue

Slot-based overlay modal with:
- **Props:** `modelValue` (Boolean, v-model for open/close), `title` (String), `maxWidth` (String, default `'480px'`)
- **Slots:** `default` (body content), `footer` (optional action buttons)
- **Behavior:** Closes on ESC keypress, closes on backdrop click, prevents body scroll when open, transitions with fade+scale
- **Structure:**
  ```
  <Teleport to="body">
    <div class="modal-overlay" @click.self="close">
      <div class="modal" :style="{ maxWidth }">
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button @click="close">close icon</button>
        </div>
        <div class="modal-body"><slot /></div>
        <div class="modal-footer" v-if="$slots.footer"><slot name="footer" /></div>
      </div>
    </div>
  </Teleport>
  ```
- **Dark mode:** Uses `var(--bg-card)`, `var(--gray-200)` for borders, `var(--bg-overlay)` for backdrop

### 1.2 ConfirmDialog.vue

Wraps BaseModal for destructive action confirmations:
- **Props:** `modelValue`, `title` (default `'Are you sure?'`), `message` (String), `confirmText` (default `'Delete'`), `variant` (one of `'danger'`, `'warning'`, default `'danger'`)
- **Emits:** `confirm`, `update:modelValue`
- **Structure:** BaseModal containing message text + Cancel/Confirm buttons. Confirm button uses `btn-danger` or `btn-warning` class based on variant.
- **Replaces:** Native `confirm()` in `ProjectDetailPage.vue` line 258 and missing confirmation in `ProfilePage.vue` line 114

### 1.3 BaseTabs.vue

Tab container with counts:
- **Props:** `tabs` (Array of `{ key: string, label: string, count?: number }`), `modelValue` (String, active tab key)
- **Emits:** `update:modelValue`
- **Structure:** Row of tab buttons with optional `(count)` suffix. Active tab has accent-colored bottom border.
- **Styling:** Matches current `.tabs` / `.tab` CSS but extracted as a reusable component

### 1.4 StatusBadge.vue

Colored status badge:
- **Props:** `status` (String), `size` (one of `'sm'`, `'md'`, default `'sm'`)
- **Color mapping:**
  - `open` → green (`#10b981`)
  - `in_progress` → amber (`#f59e0b`)
  - `closed` / `rejected` / `revision_requested` → red (`#ef4444`)
  - `pending` → gray (`#6b7280`)
  - `accepted` / `approved` / `completed` → blue/green
  - `submitted` → purple (`#8b5cf6`)
- **Structure:** `<span class="status-badge" :class="colorClass">{{ formatted }}</span>`
- **Formats:** Replaces underscores with spaces, title-cases the label

### 1.5 EmptyState.vue

Empty content placeholder:
- **Props:** `icon` (String, material icon name), `title` (String), `subtitle` (String, optional), `actionText` (String, optional), `actionTo` (String, optional router link)
- **Emits:** `action` (when action button clicked)
- **Structure:** Centered icon + title + subtitle + optional button/link
- **Replaces:** Inline empty states in ProfilePage, ChatListPage, NotificationsPage, ProjectDetailPage

### 1.6 BasePagination.vue

Page controls:
- **Props:** `currentPage` (Number), `totalPages` (Number)
- **Emits:** `update:currentPage`
- **Structure:** Prev button + page numbers (with ellipsis for large ranges) + Next button
- **Behavior:** Prev/Next disabled at boundaries. Shows up to 5 page numbers with ellipsis.

### 1.7 FormField.vue

Form input wrapper:
- **Props:** `label` (String), `error` (String, optional), `hint` (String, optional), `maxLength` (Number, optional for character counter)
- **Slots:** `default` (the actual input/textarea/select)
- **Structure:**
  ```
  <div class="form-field" :class="{ 'has-error': error }">
    <label>{{ label }}</label>
    <slot />
    <div class="field-footer">
      <span class="field-error" v-if="error">{{ error }}</span>
      <span class="field-hint" v-else-if="hint">{{ hint }}</span>
      <span class="char-count" v-if="maxLength">{{ current }}/{{ maxLength }}</span>
    </div>
  </div>
  ```
- **Styling:** Error state turns border red. Character counter right-aligned.

---

## Section 2: Company Profile

### 2.1 Layout Changes

The `ProfilePage.vue` will detect `user.role` and render a different layout per role. This is done with conditional sections inside the same component (not separate routes), since the URL stays `/profile/:id`.

**Company header** adds a 4-column info grid below the name/meta row:
- Industry, Website (clickable link), Location, Projects posted count
- These come from `GET /api/v1/users/{id}/company-profile` (already exists)
- Bio displayed below the grid

**Company tabs** (replaces Portfolio/Reviews):
1. **Projects** — list of company's own projects with status badges, application counts, deadline, spots. Each row links to `/projects/:id`. Data from `GET /api/v1/projects/?owner_id={id}` (needs a small backend addition — currently projects list can filter by `owner_id`)
2. **Applications** — consolidated view of all applications across all company projects. Shows applicant name, project title, status badge, date. Data from existing per-project application endpoints, aggregated client-side.
3. **Reviews** — same as current, no changes needed

### 2.2 Edit Modal (Company)

When company user clicks Edit on own profile, the modal shows:
- Full Name (from User model)
- Bio (from User model)
- Company Name (from CompanyProfile)
- Industry (from CompanyProfile)
- Website (from CompanyProfile)
- Description (from CompanyProfile — maps to bio display)
- Location (from CompanyProfile)

Saves via two API calls:
1. `PUT /api/v1/users/{id}` for full_name, bio
2. `PUT /api/v1/users/{id}/company-profile` for company_name, industry, website, description, location

### 2.3 API Additions (Frontend Only)

Add to `src/api/index.js` in `usersAPI`:
```javascript
getCompanyProfile: id => api.get(`/users/${id}/company-profile`),
updateCompanyProfile: (id, d) => api.put(`/users/${id}/company-profile`, d),
getStudentProfile: id => api.get(`/users/${id}/student-profile`),
updateStudentProfile: (id, d) => api.put(`/users/${id}/student-profile`, d),
```

### 2.4 Backend Addition

Add `owner_id` filter support to `GET /api/v1/projects/`:
- Already has `status` and `search` filters
- Add optional `owner_id: int = Query(None)` parameter
- Filter: `if owner_id: query = query.filter(owner_id=owner_id)`

This lets the company profile's Projects tab fetch only that company's projects.

---

## Section 3: Student Profile

### 3.1 Layout Changes

**Student header** adds:
- 4-column education grid: University, Major, Graduation Year, Completed Projects
- Data from `GET /api/v1/users/{id}/student-profile` (already exists)
- Bio displayed below

**Skills section** (below education grid, in header area):
- Skill chips displayed inline with × remove button (only visible to profile owner)
- "+ Add skill" button opens a dropdown/autocomplete that lists available skills from `GET /api/v1/skills/`
- Add via `POST /api/v1/users/{id}/skills/{skill_id}` (already exists)
- Remove via `DELETE /api/v1/users/{id}/skills/{skill_id}` (already exists)

**Student tabs:**
1. **Portfolio** — enhanced from current. Uses card grid with image placeholder area, title, description, external link, delete button (with ConfirmDialog). Add Portfolio form stays at bottom.
2. **Applications** — shows the student's applications (from `GET /api/v1/applications/my`). Each entry shows: project title, status badge (using StatusBadge), cover letter snippet, date. Replaces the separate `MyApplicationsPage.vue` content for the profile context.
3. **Reviews** — same as current

### 3.2 Edit Modal (Student)

When student clicks Edit on own profile, the modal shows:
- Full Name (from User model)
- Bio (from User model)
- University (from StudentProfile)
- Major (from StudentProfile)
- Graduation Year (from StudentProfile)

Saves via two API calls:
1. `PUT /api/v1/users/{id}` for full_name, bio
2. `PUT /api/v1/users/{id}/student-profile` for university, major, graduation_year

### 3.3 Skills Autocomplete

When "+ Add skill" is clicked:
- Shows a dropdown with search input
- Fetches all skills from `GET /api/v1/skills/`
- Filters client-side as user types
- Clicking a skill calls `POST /api/v1/users/{id}/skills/{skill_id}`
- If skill doesn't exist, option to create it (calls `POST /api/v1/skills/` then adds it)
- Implemented as a `SkillPicker.vue` component in `src/components/`

---

## Section 4: Refactoring Existing Code

### 4.1 ProfilePage.vue Restructure

Current ProfilePage.vue (163 lines) becomes the orchestrator that:
1. Loads user data + role-specific profile data
2. Renders shared header (avatar, name, username, meta)
3. Conditionally renders company info grid OR student education grid
4. Renders role-appropriate tabs via BaseTabs
5. Delegates tab content to sub-components

New file structure:
```
src/components/
  BaseModal.vue
  ConfirmDialog.vue
  BaseTabs.vue
  StatusBadge.vue
  EmptyState.vue
  BasePagination.vue
  FormField.vue
  SkillPicker.vue
  profile/
    CompanyInfoGrid.vue    — company info grid (industry, website, etc.)
    StudentInfoGrid.vue    — education grid (university, major, etc.)
    CompanyProjectsTab.vue — company's projects list
    CompanyAppsTab.vue     — consolidated applications view
    StudentPortfolioTab.vue — enhanced portfolio cards
    StudentAppsTab.vue     — student's applications
    ReviewsTab.vue         — shared reviews tab (both roles)
    EditProfileModal.vue   — role-aware edit form
```

### 4.2 ProjectDetailPage.vue Changes

- Replace `confirm('Delete this project permanently?')` with `ConfirmDialog`
- Import and use `StatusBadge` for project status display
- Import and use `EmptyState` for "No applications yet" state

### 4.3 Design Refresh

All new components and refactored code follow these refinements:
- **Border radius:** 10px for cards/modals, 6px for buttons/inputs, 16px for badges
- **Spacing:** 8px base unit (8, 12, 16, 20, 24, 32)
- **Transitions:** 150ms ease for hover/active states, 200ms for modal open/close
- **Focus states:** 2px accent-colored ring on all interactive elements
- **Dark mode:** All components use CSS variables, no hardcoded colors

---

## Files Changed Summary

### Created
- `src/components/BaseModal.vue`
- `src/components/ConfirmDialog.vue`
- `src/components/BaseTabs.vue`
- `src/components/StatusBadge.vue`
- `src/components/EmptyState.vue`
- `src/components/BasePagination.vue`
- `src/components/FormField.vue`
- `src/components/SkillPicker.vue`
- `src/components/profile/CompanyInfoGrid.vue`
- `src/components/profile/StudentInfoGrid.vue`
- `src/components/profile/CompanyProjectsTab.vue`
- `src/components/profile/CompanyAppsTab.vue`
- `src/components/profile/StudentPortfolioTab.vue`
- `src/components/profile/StudentAppsTab.vue`
- `src/components/profile/ReviewsTab.vue`
- `src/components/profile/EditProfileModal.vue`

### Modified
- `src/views/ProfilePage.vue` — major rewrite, orchestrates role-based layout
- `src/views/ProjectDetailPage.vue` — use ConfirmDialog, StatusBadge, EmptyState
- `src/api/index.js` — add company-profile, student-profile API methods
- `backend/src/projects/router.py` — add `owner_id` query filter

### Not Changed
- All other views (DashboardPage, ProjectsPage, ChatRoomPage, etc.)
- Stores (auth, toast, theme)
- Router configuration
- Backend models, services, other routers
