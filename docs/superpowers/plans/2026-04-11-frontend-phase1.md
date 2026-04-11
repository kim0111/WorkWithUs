# Frontend Phase 1: Component Library + Profile Enhancements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build 7 reusable Vue 3 components, a skill picker, and redesign the profile system so company and student users each get role-appropriate tabs and info grids.

**Architecture:** ProfilePage.vue becomes a role-based orchestrator that loads user + profile data, then delegates display to sub-components. Reusable library components (BaseModal, BaseTabs, StatusBadge, etc.) are used across both profile and project pages. All new components use `<script setup>`, scoped styles, and the existing CSS variable system.

**Tech Stack:** Vue 3 (Composition API), Vue Router, Pinia, Axios, existing CSS design system (`src/assets/styles.css`)

**Spec:** `docs/superpowers/specs/2026-04-11-frontend-phase1-design.md`

**Backend note:** The spec mentioned adding `owner_id` filter to `GET /api/v1/projects/`, but it already exists in `backend/src/projects/router.py:44`. No backend changes are needed.

---

## File Structure

### Created (16 files)
```
frontend/src/components/
  BaseModal.vue              — Slot-based overlay modal (Teleport, ESC, backdrop click, scroll lock)
  ConfirmDialog.vue          — Wraps BaseModal for destructive action confirmations
  BaseTabs.vue               — Tab container with optional counts
  StatusBadge.vue            — Colored status badge with status-to-color mapping
  EmptyState.vue             — Empty content placeholder with icon, title, optional action
  BasePagination.vue         — Page controls with prev/next and ellipsis
  FormField.vue              — Form input wrapper with label, error, hint, char counter
  SkillPicker.vue            — Searchable skill dropdown with add/create/remove
  profile/
    CompanyInfoGrid.vue      — 4-column grid: industry, website, location, project count
    StudentInfoGrid.vue      — 4-column grid: university, major, graduation year, completed
    ReviewsTab.vue           — Shared reviews list (both roles)
    CompanyProjectsTab.vue   — Company's projects list with status badges (self-loading)
    CompanyAppsTab.vue       — Consolidated applications across company projects (self-loading, owner-only)
    StudentPortfolioTab.vue  — Enhanced portfolio cards with image area, link, delete
    StudentAppsTab.vue       — Student's applications with project titles (self-loading, owner-only)
    EditProfileModal.vue     — Role-aware edit form (user fields + role-specific profile fields)
```

### Modified (3 files)
```
frontend/src/api/index.js           — Add 4 profile API methods to usersAPI
frontend/src/views/ProfilePage.vue  — Major rewrite: role-based orchestrator
frontend/src/views/ProjectDetailPage.vue — Use ConfirmDialog, StatusBadge, EmptyState
```

---

### Task 1: API Layer — Add Profile Endpoints

**Files:**
- Modify: `frontend/src/api/index.js:56-61`

- [ ] **Step 1: Add profile API methods to usersAPI**

In `frontend/src/api/index.js`, replace the `usersAPI` object (lines 56-61) with:

```javascript
export const usersAPI = {
  get: id => api.get(`/users/${id}`),
  update: (id, d) => api.put(`/users/${id}`, d),
  addSkill: (uid, sid) => api.post(`/users/${uid}/skills/${sid}`),
  removeSkill: (uid, sid) => api.delete(`/users/${uid}/skills/${sid}`),
  getCompanyProfile: id => api.get(`/users/${id}/company-profile`),
  updateCompanyProfile: (id, d) => api.put(`/users/${id}/company-profile`, d),
  getStudentProfile: id => api.get(`/users/${id}/student-profile`),
  updateStudentProfile: (id, d) => api.put(`/users/${id}/student-profile`, d),
}
```

- [ ] **Step 2: Verify the dev server starts without errors**

Run: `cd /Users/temporary/Developer/WorkWithUs/frontend && npm run dev`

Expected: Vite dev server starts on port 3000 with no compilation errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add company/student profile API methods"
```

---

### Task 2: BaseModal.vue

**Files:**
- Create: `frontend/src/components/BaseModal.vue`

- [ ] **Step 1: Create BaseModal component**

Create `frontend/src/components/BaseModal.vue`:

```vue
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <div class="modal-container" :style="{ maxWidth }">
          <div class="modal-header">
            <h3>{{ title }}</h3>
            <button class="btn btn-ghost btn-sm" @click="close">
              <span class="material-icons-round">close</span>
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, default: '' },
  maxWidth: { type: String, default: '480px' },
})

const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

function onKeydown(e) {
  if (e.key === 'Escape') close()
}

watch(() => props.modelValue, (open) => {
  if (open) {
    document.addEventListener('keydown', onKeydown)
    document.body.style.overflow = 'hidden'
  } else {
    document.removeEventListener('keydown', onKeydown)
    document.body.style.overflow = ''
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
}
.modal-container {
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  width: 100%;
  box-shadow: var(--shadow-lg);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}
.modal-body {
  padding: 16px 24px 24px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 24px 20px;
}
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-container {
  transform: scale(0.95);
}
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
```

- [ ] **Step 2: Verify dev server compiles without errors**

Run: `cd /Users/temporary/Developer/WorkWithUs/frontend && npm run dev`

Expected: No compilation errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BaseModal.vue
git commit -m "feat: add BaseModal reusable component"
```

---

### Task 3: ConfirmDialog.vue

**Files:**
- Create: `frontend/src/components/ConfirmDialog.vue`

**Depends on:** Task 2 (BaseModal)

- [ ] **Step 1: Create ConfirmDialog component**

Create `frontend/src/components/ConfirmDialog.vue`:

```vue
<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" :title="title">
    <p class="confirm-message">{{ message }}</p>
    <template #footer>
      <button class="btn btn-secondary btn-sm" @click="$emit('update:modelValue', false)">Cancel</button>
      <button class="btn btn-sm" :class="confirmClass" @click="$emit('confirm')">{{ confirmText }}</button>
    </template>
  </BaseModal>
</template>

<script setup>
import { computed } from 'vue'
import BaseModal from '@/components/BaseModal.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: 'Delete' },
  variant: { type: String, default: 'danger' },
})

defineEmits(['update:modelValue', 'confirm'])

const confirmClass = computed(() =>
  props.variant === 'warning' ? 'btn-warning' : 'btn-danger'
)
</script>

<style scoped>
.confirm-message {
  color: var(--gray-600);
  font-size: 0.875rem;
  line-height: 1.6;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ConfirmDialog.vue
git commit -m "feat: add ConfirmDialog reusable component"
```

---

### Task 4: BaseTabs.vue

**Files:**
- Create: `frontend/src/components/BaseTabs.vue`

- [ ] **Step 1: Create BaseTabs component**

Create `frontend/src/components/BaseTabs.vue`:

```vue
<template>
  <div class="base-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="base-tab"
      :class="{ active: modelValue === tab.key }"
      @click="$emit('update:modelValue', tab.key)"
    >
      {{ tab.label }}<span v-if="tab.count != null" class="tab-count">({{ tab.count }})</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.base-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--gray-200);
  margin-bottom: 1.5rem;
}
.base-tab {
  padding: 10px 20px;
  border: none;
  background: none;
  color: var(--gray-500);
  font-family: var(--font);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s ease;
}
.base-tab.active {
  color: var(--accent-text);
  border-bottom-color: var(--accent);
  font-weight: 600;
}
.base-tab:hover {
  color: var(--gray-700);
}
.tab-count {
  margin-left: 4px;
  color: var(--gray-400);
  font-weight: 400;
}
.base-tab.active .tab-count {
  color: var(--accent-text);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/BaseTabs.vue
git commit -m "feat: add BaseTabs reusable component"
```

---

### Task 5: StatusBadge.vue

**Files:**
- Create: `frontend/src/components/StatusBadge.vue`

- [ ] **Step 1: Create StatusBadge component**

Create `frontend/src/components/StatusBadge.vue`:

```vue
<template>
  <span class="status-badge" :class="[colorClass, sizeClass]">{{ formatted }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'sm' },
})

const colorMap = {
  open: 'status-green',
  in_progress: 'status-amber',
  closed: 'status-red',
  rejected: 'status-red',
  revision_requested: 'status-red',
  pending: 'status-gray',
  accepted: 'status-green',
  approved: 'status-green',
  completed: 'status-green',
  submitted: 'status-purple',
}

const colorClass = computed(() => colorMap[props.status] || 'status-gray')
const sizeClass = computed(() => props.size === 'md' ? 'status-md' : 'status-sm')
const formatted = computed(() =>
  props.status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
)
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 16px;
  font-weight: 500;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.status-sm {
  padding: 2px 8px;
  font-size: 0.6875rem;
}
.status-md {
  padding: 3px 10px;
  font-size: 0.75rem;
}
.status-green {
  background: var(--success-light);
  color: var(--success);
}
.status-amber {
  background: var(--warning-light);
  color: var(--warning);
}
.status-red {
  background: var(--danger-light);
  color: var(--danger);
}
.status-gray {
  background: var(--gray-100);
  color: var(--gray-500);
}
.status-purple {
  background: #f3e8ff;
  color: #7c3aed;
}
[data-theme="dark"] .status-purple {
  background: #2e1065;
  color: #c4b5fd;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/StatusBadge.vue
git commit -m "feat: add StatusBadge reusable component"
```

---

### Task 6: EmptyState.vue

**Files:**
- Create: `frontend/src/components/EmptyState.vue`

- [ ] **Step 1: Create EmptyState component**

Create `frontend/src/components/EmptyState.vue`:

```vue
<template>
  <div class="empty-state-wrapper">
    <span class="material-icons-round empty-icon">{{ icon }}</span>
    <h3>{{ title }}</h3>
    <p v-if="subtitle">{{ subtitle }}</p>
    <router-link v-if="actionText && actionTo" :to="actionTo" class="btn btn-primary btn-sm">{{ actionText }}</router-link>
    <button v-else-if="actionText" class="btn btn-primary btn-sm" @click="$emit('action')">{{ actionText }}</button>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  actionText: { type: String, default: '' },
  actionTo: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 8px;
  text-align: center;
}
.empty-icon {
  font-size: 48px;
  color: var(--gray-300);
}
.empty-state-wrapper h3 {
  color: var(--gray-600);
  font-weight: 500;
}
.empty-state-wrapper p {
  color: var(--gray-400);
  font-size: 0.875rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/EmptyState.vue
git commit -m "feat: add EmptyState reusable component"
```

---

### Task 7: BasePagination.vue

**Files:**
- Create: `frontend/src/components/BasePagination.vue`

- [ ] **Step 1: Create BasePagination component**

Create `frontend/src/components/BasePagination.vue`:

```vue
<template>
  <div v-if="totalPages > 1" class="pagination">
    <button class="btn btn-ghost btn-sm" :disabled="currentPage <= 1" @click="go(currentPage - 1)">
      <span class="material-icons-round">chevron_left</span>
    </button>
    <template v-for="p in pages" :key="p">
      <span v-if="p === '...'" class="pagination-ellipsis">...</span>
      <button
        v-else
        class="btn btn-sm pagination-page"
        :class="{ 'pagination-active': p === currentPage }"
        @click="go(p)"
      >{{ p }}</button>
    </template>
    <button class="btn btn-ghost btn-sm" :disabled="currentPage >= totalPages" @click="go(currentPage + 1)">
      <span class="material-icons-round">chevron_right</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
})

const emit = defineEmits(['update:currentPage'])

function go(page) {
  if (page >= 1 && page <= props.totalPages) {
    emit('update:currentPage', page)
  }
}

const pages = computed(() => {
  const total = props.totalPages
  const current = props.currentPage
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)

  const result = []
  result.push(1)
  if (current > 3) result.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    result.push(i)
  }
  if (current < total - 2) result.push('...')
  result.push(total)
  return result
})
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 1.5rem;
}
.pagination-ellipsis {
  padding: 4px 6px;
  color: var(--gray-400);
  font-size: 0.8125rem;
}
.pagination-page {
  background: none;
  color: var(--gray-600);
  border: 1px solid transparent;
  min-width: 32px;
  justify-content: center;
}
.pagination-page:hover {
  background: var(--gray-100);
}
.pagination-active {
  background: var(--accent) !important;
  color: #fff !important;
  border-color: var(--accent);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/BasePagination.vue
git commit -m "feat: add BasePagination reusable component"
```

---

### Task 8: FormField.vue

**Files:**
- Create: `frontend/src/components/FormField.vue`

- [ ] **Step 1: Create FormField component**

Create `frontend/src/components/FormField.vue`:

```vue
<template>
  <div class="form-field" :class="{ 'has-error': error }">
    <label class="field-label">{{ label }}</label>
    <slot />
    <div class="field-footer">
      <span v-if="error" class="field-error">{{ error }}</span>
      <span v-else-if="hint" class="field-hint">{{ hint }}</span>
      <span v-if="maxLength" class="char-count">{{ currentLength }}/{{ maxLength }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, useSlots } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  maxLength: { type: Number, default: 0 },
})

const currentLength = ref(0)

function updateLength() {
  if (!props.maxLength) return
  const el = document.querySelector('.form-field.counting input, .form-field.counting textarea')
  if (el) currentLength.value = el.value.length
}
</script>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--gray-700);
}
.field-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 18px;
}
.field-error {
  color: var(--danger);
  font-size: 0.75rem;
}
.field-hint {
  color: var(--gray-400);
  font-size: 0.75rem;
}
.char-count {
  color: var(--gray-400);
  font-size: 0.75rem;
  margin-left: auto;
}
.has-error :slotted(input),
.has-error :slotted(textarea),
.has-error :slotted(select) {
  border-color: var(--danger);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/FormField.vue
git commit -m "feat: add FormField reusable component"
```

---

### Task 9: SkillPicker.vue

**Files:**
- Create: `frontend/src/components/SkillPicker.vue`

**Depends on:** Task 1 (API layer)

- [ ] **Step 1: Create SkillPicker component**

Create `frontend/src/components/SkillPicker.vue`:

```vue
<template>
  <div class="skill-picker">
    <div class="skill-chips">
      <span v-for="s in skills" :key="s.id" class="skill-chip">
        {{ s.name }}
        <button v-if="editable" class="chip-remove" @click="removeSkill(s.id)">&times;</button>
      </span>
      <button v-if="editable" class="add-skill-btn" @click="showDropdown = !showDropdown">+ Add skill</button>
    </div>

    <div v-if="showDropdown" class="skill-dropdown">
      <input
        ref="searchInput"
        class="input skill-search"
        v-model="search"
        placeholder="Search skills..."
        @keydown.escape="showDropdown = false"
      />
      <div class="skill-options">
        <button
          v-for="s in filtered"
          :key="s.id"
          class="skill-option"
          @click="addSkill(s.id)"
        >{{ s.name }}</button>
        <button v-if="search.trim() && !exactMatch" class="skill-option skill-create" @click="createAndAdd">
          Create "{{ search.trim() }}"
        </button>
        <div v-if="!filtered.length && !search.trim()" class="skill-empty">No skills available</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { skillsAPI, usersAPI } from '@/api'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  skills: { type: Array, default: () => [] },
  userId: { type: Number, required: true },
  editable: { type: Boolean, default: false },
})

const emit = defineEmits(['updated'])

const toast = useToastStore()
const allSkills = ref([])
const search = ref('')
const showDropdown = ref(false)
const searchInput = ref(null)

const filtered = computed(() => {
  const currentIds = new Set(props.skills.map(s => s.id))
  let list = allSkills.value.filter(s => !currentIds.has(s.id))
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(q))
  }
  return list
})

const exactMatch = computed(() => {
  const q = search.value.trim().toLowerCase()
  return allSkills.value.some(s => s.name.toLowerCase() === q)
})

watch(showDropdown, async (open) => {
  if (open) {
    try { allSkills.value = (await skillsAPI.list()).data } catch {}
    await nextTick()
    searchInput.value?.focus()
  } else {
    search.value = ''
  }
})

async function addSkill(skillId) {
  try {
    await usersAPI.addSkill(props.userId, skillId)
    showDropdown.value = false
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to add skill')
  }
}

async function removeSkill(skillId) {
  try {
    await usersAPI.removeSkill(props.userId, skillId)
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to remove skill')
  }
}

async function createAndAdd() {
  try {
    const { data } = await skillsAPI.create({ name: search.value.trim() })
    await addSkill(data.id)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create skill')
  }
}
</script>

<style scoped>
.skill-picker {
  position: relative;
}
.skill-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.skill-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: var(--accent-light);
  color: var(--accent-text);
  border-radius: 16px;
  font-size: 0.8125rem;
}
.chip-remove {
  background: none;
  border: none;
  color: var(--accent-text);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
}
.chip-remove:hover {
  opacity: 1;
}
.add-skill-btn {
  background: transparent;
  border: 1px dashed var(--gray-300);
  color: var(--gray-500);
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.8125rem;
  font-family: var(--font);
  cursor: pointer;
  transition: all 0.15s ease;
}
.add-skill-btn:hover {
  border-color: var(--accent);
  color: var(--accent-text);
}
.skill-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  width: 280px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 50;
  overflow: hidden;
}
.skill-search {
  border: none;
  border-bottom: 1px solid var(--gray-200);
  border-radius: 0;
  font-size: 0.8125rem;
}
.skill-search:focus {
  box-shadow: none;
}
.skill-options {
  max-height: 200px;
  overflow-y: auto;
}
.skill-option {
  display: block;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  text-align: left;
  font-family: var(--font);
  font-size: 0.8125rem;
  color: var(--gray-700);
  cursor: pointer;
}
.skill-option:hover {
  background: var(--gray-100);
}
.skill-create {
  color: var(--accent-text);
  font-weight: 500;
}
.skill-empty {
  padding: 12px;
  text-align: center;
  color: var(--gray-400);
  font-size: 0.8125rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SkillPicker.vue
git commit -m "feat: add SkillPicker component with search and create"
```

---

### Task 10: CompanyInfoGrid.vue and StudentInfoGrid.vue

**Files:**
- Create: `frontend/src/components/profile/CompanyInfoGrid.vue`
- Create: `frontend/src/components/profile/StudentInfoGrid.vue`

- [ ] **Step 1: Create the profile directory**

```bash
mkdir -p frontend/src/components/profile
```

- [ ] **Step 2: Create CompanyInfoGrid component**

Create `frontend/src/components/profile/CompanyInfoGrid.vue`:

```vue
<template>
  <div class="info-grid">
    <div class="info-item">
      <div class="info-label">Industry</div>
      <div class="info-value">{{ profile?.industry || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Website</div>
      <div class="info-value">
        <a v-if="profile?.website" :href="websiteUrl" target="_blank" class="info-link">{{ profile.website }}</a>
        <span v-else>Not specified</span>
      </div>
    </div>
    <div class="info-item">
      <div class="info-label">Location</div>
      <div class="info-value">{{ profile?.location || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Projects</div>
      <div class="info-value">{{ projectCount }} posted</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, default: null },
  projectCount: { type: Number, default: 0 },
})

const websiteUrl = computed(() => {
  const url = props.profile?.website || ''
  return url.startsWith('http') ? url : `https://${url}`
})
</script>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-200);
}
.info-label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  color: var(--gray-400);
  letter-spacing: 0.5px;
  font-weight: 500;
}
.info-value {
  font-size: 0.875rem;
  margin-top: 4px;
  color: var(--gray-900);
}
.info-link {
  color: var(--accent-text);
  font-size: 0.875rem;
}
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
```

- [ ] **Step 3: Create StudentInfoGrid component**

Create `frontend/src/components/profile/StudentInfoGrid.vue`:

```vue
<template>
  <div class="info-grid">
    <div class="info-item">
      <div class="info-label">University</div>
      <div class="info-value">{{ profile?.university || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Major</div>
      <div class="info-value">{{ profile?.major || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Graduation</div>
      <div class="info-value">{{ profile?.graduation_year || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Completed</div>
      <div class="info-value">{{ profile?.completed_projects_count || 0 }} projects</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  profile: { type: Object, default: null },
})
</script>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-200);
}
.info-label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  color: var(--gray-400);
  letter-spacing: 0.5px;
  font-weight: 500;
}
.info-value {
  font-size: 0.875rem;
  margin-top: 4px;
  color: var(--gray-900);
}
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/profile/CompanyInfoGrid.vue frontend/src/components/profile/StudentInfoGrid.vue
git commit -m "feat: add CompanyInfoGrid and StudentInfoGrid components"
```

---

### Task 11: ReviewsTab.vue

**Files:**
- Create: `frontend/src/components/profile/ReviewsTab.vue`

- [ ] **Step 1: Create ReviewsTab component**

Create `frontend/src/components/profile/ReviewsTab.vue`:

```vue
<template>
  <div>
    <div v-if="reviews.length" class="reviews-list">
      <div v-for="r in reviews" :key="r.id" class="review-card card">
        <div class="review-header">
          <div class="stars">{{ '\u2605'.repeat(Math.round(r.rating)) }}{{ '\u2606'.repeat(5 - Math.round(r.rating)) }}</div>
          <span class="text-muted">{{ fmtDate(r.created_at) }}</span>
        </div>
        <p v-if="r.comment" class="review-comment">{{ r.comment }}</p>
        <span class="badge badge-info review-type">{{ r.review_type }}</span>
      </div>
    </div>
    <EmptyState v-else icon="star_outline" title="No reviews yet" subtitle="Reviews will appear here after project collaborations" />
  </div>
</template>

<script setup>
import EmptyState from '@/components/EmptyState.vue'

defineProps({
  reviews: { type: Array, default: () => [] },
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}
</script>

<style scoped>
.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.review-card {
  padding: 16px;
}
.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.stars {
  color: var(--warning);
  font-size: 1.1rem;
  letter-spacing: 1px;
}
.review-comment {
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
}
.review-type {
  margin-top: 6px;
}
.text-muted {
  color: var(--gray-400);
  font-size: 0.8125rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/ReviewsTab.vue
git commit -m "feat: add ReviewsTab shared profile component"
```

---

### Task 12: CompanyProjectsTab.vue

**Files:**
- Create: `frontend/src/components/profile/CompanyProjectsTab.vue`

**Depends on:** Tasks 1, 5 (API, StatusBadge)

- [ ] **Step 1: Create CompanyProjectsTab component**

Create `frontend/src/components/profile/CompanyProjectsTab.vue`:

```vue
<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="projects.length" class="projects-list">
        <router-link
          v-for="p in projects"
          :key="p.id"
          :to="`/projects/${p.id}`"
          class="project-row card card-interactive"
        >
          <div class="project-row-main">
            <div class="project-row-info">
              <div class="project-row-title">
                <span class="project-name">{{ p.title }}</span>
                <StatusBadge :status="p.status" />
              </div>
              <div class="project-row-meta">
                {{ p.max_participants }} spots &middot;
                <template v-if="p.deadline">Deadline: {{ fmtDate(p.deadline) }} &middot;</template>
                {{ applicationCounts[p.id] || 0 }} applications
              </div>
            </div>
            <span class="material-icons-round project-arrow">chevron_right</span>
          </div>
        </router-link>
      </div>
      <EmptyState v-else icon="folder_open" title="No projects yet" subtitle="Projects created by this company will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectsAPI, applicationsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps({
  userId: { type: Number, required: true },
  isOwner: { type: Boolean, default: false },
})

const projects = ref([])
const applicationCounts = ref({})
const loading = ref(true)

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: props.userId, size: 100 })
    projects.value = data.items || []

    if (props.isOwner) {
      const counts = {}
      await Promise.all(
        projects.value.map(async (p) => {
          try {
            const res = await applicationsAPI.byProject(p.id)
            counts[p.id] = res.data.length
          } catch {
            counts[p.id] = 0
          }
        })
      )
      applicationCounts.value = counts
    }
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.projects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.project-row {
  text-decoration: none;
  color: inherit;
  padding: 16px 20px;
}
.project-row:hover {
  text-decoration: none;
}
.project-row-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.project-row-info {
  flex: 1;
}
.project-row-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.project-name {
  font-weight: 600;
  font-size: 0.9375rem;
}
.project-row-meta {
  color: var(--gray-400);
  font-size: 0.8125rem;
  margin-top: 4px;
}
.project-arrow {
  color: var(--gray-400);
  font-size: 20px;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/CompanyProjectsTab.vue
git commit -m "feat: add CompanyProjectsTab profile component"
```

---

### Task 13: CompanyAppsTab.vue

**Files:**
- Create: `frontend/src/components/profile/CompanyAppsTab.vue`

**Depends on:** Tasks 1, 5 (API, StatusBadge)

- [ ] **Step 1: Create CompanyAppsTab component**

Create `frontend/src/components/profile/CompanyAppsTab.vue`:

```vue
<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="apps.length" class="apps-list">
        <div v-for="a in apps" :key="a.id" class="app-row card">
          <div class="app-row-header">
            <router-link :to="`/profile/${a.applicant_id}`" class="applicant-link">
              <div class="av-sm">{{ String(a.applicant_id).charAt(0) }}</div>
              User #{{ a.applicant_id }}
            </router-link>
            <StatusBadge :status="a.status" />
          </div>
          <div class="app-row-meta">
            <span class="project-title">{{ a._projectTitle }}</span>
            <span class="text-muted">&middot; {{ fmtDate(a.created_at) }}</span>
          </div>
          <p v-if="a.cover_letter" class="app-row-cl">{{ a.cover_letter }}</p>
        </div>
      </div>
      <EmptyState v-else icon="inbox" title="No applications yet" subtitle="Applications to your projects will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectsAPI, applicationsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps({
  userId: { type: Number, required: true },
})

const apps = ref([])
const loading = ref(true)

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: props.userId, size: 100 })
    const projects = data.items || []
    const allApps = []

    await Promise.all(
      projects.map(async (p) => {
        try {
          const res = await applicationsAPI.byProject(p.id)
          for (const a of res.data) {
            a._projectTitle = p.title
            allApps.push(a)
          }
        } catch {}
      })
    )

    allApps.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    apps.value = allApps
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.apps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.app-row {
  padding: 16px;
}
.app-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.applicant-link {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--gray-900);
  font-weight: 500;
  font-size: 0.875rem;
}
.av-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.7rem;
  color: white;
}
.app-row-meta {
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 6px;
}
.project-title {
  color: var(--accent-text);
  font-weight: 500;
}
.text-muted {
  color: var(--gray-400);
}
.app-row-cl {
  margin-top: 8px;
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/CompanyAppsTab.vue
git commit -m "feat: add CompanyAppsTab profile component"
```

---

### Task 14: StudentPortfolioTab.vue

**Files:**
- Create: `frontend/src/components/profile/StudentPortfolioTab.vue`

**Depends on:** Task 3 (ConfirmDialog)

- [ ] **Step 1: Create StudentPortfolioTab component**

Create `frontend/src/components/profile/StudentPortfolioTab.vue`:

```vue
<template>
  <div>
    <div v-if="portfolio.length" class="portfolio-grid">
      <div v-for="p in portfolio" :key="p.id" class="portfolio-card">
        <div class="portfolio-image">
          <span class="material-icons-round">code</span>
        </div>
        <div class="portfolio-body">
          <h4>{{ p.title }}</h4>
          <p v-if="p.description" class="portfolio-desc">{{ p.description }}</p>
          <div class="portfolio-footer">
            <a v-if="p.project_url" :href="p.project_url" target="_blank" class="portfolio-link">
              View project <span class="material-icons-round">open_in_new</span>
            </a>
            <button v-if="isOwner" class="btn btn-ghost btn-sm del-btn" @click="confirmDelete(p.id)">
              <span class="material-icons-round">delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <EmptyState v-else icon="collections" title="No portfolio items" subtitle="Showcase your work by adding portfolio items" />

    <div v-if="isOwner" class="add-portfolio">
      <h3>Add Portfolio Item</h3>
      <form @submit.prevent="addItem" class="pf-form">
        <input class="input" v-model="form.title" placeholder="Title" required />
        <input class="input" v-model="form.description" placeholder="Description" />
        <input class="input" v-model="form.project_url" placeholder="URL (optional)" />
        <button type="submit" class="btn btn-primary btn-sm">Add</button>
      </form>
    </div>

    <ConfirmDialog
      v-model="showConfirm"
      title="Delete Portfolio Item"
      message="This portfolio item will be permanently removed."
      @confirm="doDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { portfolioAPI } from '@/api'
import { useToastStore } from '@/stores/toast'
import EmptyState from '@/components/EmptyState.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const props = defineProps({
  portfolio: { type: Array, default: () => [] },
  isOwner: { type: Boolean, default: false },
})

const emit = defineEmits(['updated'])

const toast = useToastStore()
const form = reactive({ title: '', description: '', project_url: '' })
const showConfirm = ref(false)
const deleteId = ref(null)

function confirmDelete(id) {
  deleteId.value = id
  showConfirm.value = true
}

async function doDelete() {
  showConfirm.value = false
  try {
    await portfolioAPI.delete(deleteId.value)
    toast.success('Portfolio item deleted')
    emit('updated')
  } catch {
    toast.error('Failed to delete')
  }
}

async function addItem() {
  try {
    await portfolioAPI.add(form)
    toast.success('Added!')
    form.title = ''
    form.description = ''
    form.project_url = ''
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed')
  }
}
</script>

<style scoped>
.portfolio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 1.5rem;
}
.portfolio-card {
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  overflow: hidden;
  background: var(--white);
}
.portfolio-image {
  height: 120px;
  background: var(--gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
}
.portfolio-image .material-icons-round {
  font-size: 32px;
  color: var(--gray-300);
}
.portfolio-body {
  padding: 14px 16px;
}
.portfolio-body h4 {
  font-size: 0.875rem;
  margin-bottom: 4px;
}
.portfolio-desc {
  color: var(--gray-500);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.portfolio-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.portfolio-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8125rem;
  color: var(--accent-text);
}
.portfolio-link .material-icons-round {
  font-size: 14px;
}
.del-btn {
  color: var(--gray-400);
}
.del-btn:hover {
  color: var(--danger);
}
.add-portfolio {
  padding-top: 0.75rem;
  border-top: 1px solid var(--gray-200);
}
.add-portfolio h3 {
  margin-bottom: 10px;
  font-size: 0.9375rem;
}
.pf-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 440px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/StudentPortfolioTab.vue
git commit -m "feat: add StudentPortfolioTab with ConfirmDialog integration"
```

---

### Task 15: StudentAppsTab.vue

**Files:**
- Create: `frontend/src/components/profile/StudentAppsTab.vue`

**Depends on:** Tasks 1, 5 (API, StatusBadge)

- [ ] **Step 1: Create StudentAppsTab component**

Create `frontend/src/components/profile/StudentAppsTab.vue`:

```vue
<template>
  <div>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <template v-else>
      <div v-if="apps.length" class="apps-list">
        <router-link
          v-for="a in apps"
          :key="a.id"
          :to="`/projects/${a.project_id}`"
          class="app-row card card-interactive"
        >
          <div class="app-row-header">
            <span class="app-project-title">{{ a._projectTitle || `Project #${a.project_id}` }}</span>
            <StatusBadge :status="a.status" />
          </div>
          <p v-if="a.cover_letter" class="app-row-cl">{{ a.cover_letter }}</p>
          <div class="app-row-meta">
            <span class="text-muted">Applied {{ fmtDate(a.created_at) }}</span>
          </div>
        </router-link>
      </div>
      <EmptyState v-else icon="description" title="No applications yet" subtitle="Your project applications will appear here" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { applicationsAPI, projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const apps = ref([])
const loading = ref(true)

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  try {
    const { data } = await applicationsAPI.my()
    const projectIds = [...new Set(data.map(a => a.project_id))]
    const projectMap = {}
    await Promise.all(
      projectIds.map(async (pid) => {
        try {
          const res = await projectsAPI.get(pid)
          projectMap[pid] = res.data.title
        } catch {}
      })
    )
    apps.value = data.map(a => ({ ...a, _projectTitle: projectMap[a.project_id] || '' }))
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.apps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.app-row {
  padding: 16px;
  text-decoration: none;
  color: inherit;
  display: block;
}
.app-row:hover {
  text-decoration: none;
}
.app-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.app-project-title {
  font-weight: 600;
  font-size: 0.9375rem;
}
.app-row-cl {
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}
.app-row-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.text-muted {
  color: var(--gray-400);
  font-size: 0.8125rem;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/StudentAppsTab.vue
git commit -m "feat: add StudentAppsTab profile component"
```

---

### Task 16: EditProfileModal.vue

**Files:**
- Create: `frontend/src/components/profile/EditProfileModal.vue`

**Depends on:** Tasks 1, 2, 8 (API, BaseModal, FormField)

- [ ] **Step 1: Create EditProfileModal component**

Create `frontend/src/components/profile/EditProfileModal.vue`:

```vue
<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" title="Edit Profile" maxWidth="520px">
    <form @submit.prevent="save" class="edit-form">
      <FormField label="Full Name">
        <input class="input" v-model="form.full_name" />
      </FormField>
      <FormField label="Bio">
        <textarea class="input" v-model="form.bio" rows="3"></textarea>
      </FormField>

      <template v-if="role === 'company'">
        <FormField label="Company Name">
          <input class="input" v-model="profileForm.company_name" />
        </FormField>
        <FormField label="Industry">
          <input class="input" v-model="profileForm.industry" />
        </FormField>
        <FormField label="Website">
          <input class="input" v-model="profileForm.website" placeholder="https://..." />
        </FormField>
        <FormField label="Description">
          <textarea class="input" v-model="profileForm.description" rows="3"></textarea>
        </FormField>
        <FormField label="Location">
          <input class="input" v-model="profileForm.location" />
        </FormField>
      </template>

      <template v-if="role === 'student'">
        <FormField label="University">
          <input class="input" v-model="profileForm.university" />
        </FormField>
        <FormField label="Major">
          <input class="input" v-model="profileForm.major" />
        </FormField>
        <FormField label="Graduation Year">
          <input class="input" type="number" v-model.number="profileForm.graduation_year" />
        </FormField>
      </template>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('update:modelValue', false)">Cancel</button>
        <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { usersAPI } from '@/api'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  user: { type: Object, required: true },
  profile: { type: Object, default: null },
  role: { type: String, required: true },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const toast = useToastStore()
const saving = ref(false)

const form = reactive({ full_name: '', bio: '' })
const profileForm = reactive({
  company_name: '',
  industry: '',
  website: '',
  description: '',
  location: '',
  university: '',
  major: '',
  graduation_year: null,
})

watch(() => props.modelValue, (open) => {
  if (open) {
    form.full_name = props.user.full_name || ''
    form.bio = props.user.bio || ''
    if (props.role === 'company' && props.profile) {
      profileForm.company_name = props.profile.company_name || ''
      profileForm.industry = props.profile.industry || ''
      profileForm.website = props.profile.website || ''
      profileForm.description = props.profile.description || ''
      profileForm.location = props.profile.location || ''
    }
    if (props.role === 'student' && props.profile) {
      profileForm.university = props.profile.university || ''
      profileForm.major = props.profile.major || ''
      profileForm.graduation_year = props.profile.graduation_year || null
    }
  }
})

async function save() {
  saving.value = true
  try {
    await usersAPI.update(props.user.id, { full_name: form.full_name, bio: form.bio })

    if (props.role === 'company') {
      await usersAPI.updateCompanyProfile(props.user.id, {
        company_name: profileForm.company_name,
        industry: profileForm.industry,
        website: profileForm.website,
        description: profileForm.description,
        location: profileForm.location,
      })
    }
    if (props.role === 'student') {
      await usersAPI.updateStudentProfile(props.user.id, {
        university: profileForm.university,
        major: profileForm.major,
        graduation_year: profileForm.graduation_year,
      })
    }

    toast.success('Profile updated')
    emit('update:modelValue', false)
    emit('saved')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to save')
  }
  saving.value = false
}
</script>

<style scoped>
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/profile/EditProfileModal.vue
git commit -m "feat: add EditProfileModal with role-aware fields"
```

---

### Task 17: ProfilePage.vue Rewrite

**Files:**
- Modify: `frontend/src/views/ProfilePage.vue` (full rewrite — 163 lines → ~200 lines)

**Depends on:** All previous tasks (1-16)

- [ ] **Step 1: Rewrite ProfilePage.vue as role-based orchestrator**

Replace the entire content of `frontend/src/views/ProfilePage.vue` with:

```vue
<template>
  <div v-if="user" class="page container">
    <!-- Shared Header -->
    <div class="profile-header">
      <div class="profile-avatar">{{ (user.full_name || user.username)[0].toUpperCase() }}</div>
      <div class="profile-info">
        <div class="profile-name-row">
          <h1>{{ user.full_name || user.username }}</h1>
          <span class="badge" :class="roleBadge">{{ user.role }}</span>
        </div>
        <p class="profile-username">@{{ user.username }}</p>
        <div class="profile-meta">
          <span><span class="material-icons-round">email</span>{{ user.email }}</span>
          <span><span class="material-icons-round">calendar_today</span>Joined {{ fmtDate(user.created_at) }}</span>
          <span v-if="rating"><span class="material-icons-round">star</span>{{ rating.average_rating }}/5 ({{ rating.total_reviews }} reviews)</span>
        </div>
      </div>
      <button v-if="isMe" class="btn btn-secondary btn-sm" @click="showEdit = true">
        <span class="material-icons-round">edit</span>Edit
      </button>
    </div>

    <!-- Role-specific Info Grid -->
    <CompanyInfoGrid v-if="isCompany" :profile="roleProfile" :projectCount="projectCount" />
    <StudentInfoGrid v-if="isStudent" :profile="roleProfile" />

    <!-- Bio -->
    <p v-if="displayBio" class="profile-bio">{{ displayBio }}</p>

    <!-- Skills (student) -->
    <SkillPicker
      v-if="isStudent"
      :skills="user.skills || []"
      :userId="user.id"
      :editable="isMe"
      @updated="reload"
      class="profile-skills-section"
    />

    <!-- Tabs -->
    <BaseTabs :tabs="tabList" v-model="activeTab" />

    <!-- Tab Content -->
    <section class="tab-content">
      <!-- Company tabs -->
      <CompanyProjectsTab v-if="isCompany && activeTab === 'projects'" :userId="user.id" :isOwner="isMe" />
      <CompanyAppsTab v-if="isCompany && activeTab === 'applications' && isMe" :userId="user.id" />

      <!-- Student tabs -->
      <StudentPortfolioTab v-if="isStudent && activeTab === 'portfolio'" :portfolio="portfolio" :isOwner="isMe" @updated="reload" />
      <StudentAppsTab v-if="isStudent && activeTab === 'applications' && isMe" />

      <!-- Shared -->
      <ReviewsTab v-if="activeTab === 'reviews'" :reviews="reviews" />
    </section>

    <!-- Edit Modal -->
    <EditProfileModal
      v-model="showEdit"
      :user="user"
      :profile="roleProfile"
      :role="user.role"
      @saved="onSaved"
    />
  </div>
  <div v-else class="loading-center"><div class="spinner"></div></div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usersAPI, portfolioAPI, reviewsAPI, projectsAPI } from '@/api'

import BaseTabs from '@/components/BaseTabs.vue'
import SkillPicker from '@/components/SkillPicker.vue'
import CompanyInfoGrid from '@/components/profile/CompanyInfoGrid.vue'
import StudentInfoGrid from '@/components/profile/StudentInfoGrid.vue'
import CompanyProjectsTab from '@/components/profile/CompanyProjectsTab.vue'
import CompanyAppsTab from '@/components/profile/CompanyAppsTab.vue'
import StudentPortfolioTab from '@/components/profile/StudentPortfolioTab.vue'
import StudentAppsTab from '@/components/profile/StudentAppsTab.vue'
import ReviewsTab from '@/components/profile/ReviewsTab.vue'
import EditProfileModal from '@/components/profile/EditProfileModal.vue'

const route = useRoute()
const auth = useAuthStore()

const user = ref(null)
const roleProfile = ref(null)
const portfolio = ref([])
const reviews = ref([])
const rating = ref(null)
const projectCount = ref(0)
const activeTab = ref('')
const showEdit = ref(false)

const isMe = computed(() => auth.user?.id === Number(route.params.id))
const isCompany = computed(() => user.value?.role === 'company')
const isStudent = computed(() => user.value?.role === 'student')
const roleBadge = computed(() => ({
  student: 'badge-teal',
  company: 'badge-accent',
  admin: 'badge-danger',
  committee: 'badge-info',
}[user.value?.role]))

const displayBio = computed(() => {
  if (isCompany.value && roleProfile.value?.description) return roleProfile.value.description
  return user.value?.bio || ''
})

const tabList = computed(() => {
  if (isCompany.value) {
    const tabs = [
      { key: 'projects', label: 'Projects', count: projectCount.value },
    ]
    if (isMe.value) tabs.push({ key: 'applications', label: 'Applications' })
    tabs.push({ key: 'reviews', label: 'Reviews', count: rating.value?.total_reviews })
    return tabs
  }
  const tabs = [
    { key: 'portfolio', label: 'Portfolio', count: portfolio.value.length },
  ]
  if (isMe.value) tabs.push({ key: 'applications', label: 'Applications' })
  tabs.push({ key: 'reviews', label: 'Reviews', count: rating.value?.total_reviews })
  return tabs
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

async function reload() {
  await load()
}

async function onSaved() {
  await reload()
  await auth.fetchUser()
}

async function load() {
  const id = route.params.id
  try {
    user.value = (await usersAPI.get(id)).data
  } catch {
    return
  }

  // Load role-specific profile
  if (isCompany.value) {
    try { roleProfile.value = (await usersAPI.getCompanyProfile(id)).data } catch { roleProfile.value = null }
    try {
      const { data } = await projectsAPI.list({ owner_id: id, size: 1 })
      projectCount.value = data.total
    } catch { projectCount.value = 0 }
  } else if (isStudent.value) {
    try { roleProfile.value = (await usersAPI.getStudentProfile(id)).data } catch { roleProfile.value = null }
    try { portfolio.value = (await portfolioAPI.byUser(id)).data } catch { portfolio.value = [] }
  }

  try { reviews.value = (await reviewsAPI.forUser(id)).data } catch { reviews.value = [] }
  try { rating.value = (await reviewsAPI.rating(id)).data } catch { rating.value = null }

  // Set default tab
  if (!activeTab.value) {
    activeTab.value = isCompany.value ? 'projects' : 'portfolio'
  }
}

watch(() => route.params.id, () => {
  activeTab.value = ''
  load()
})

onMounted(load)
</script>

<style scoped>
.page {
  padding: 2rem 24px;
}
.profile-header {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  padding-bottom: 1.5rem;
}
.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}
.profile-info {
  flex: 1;
}
.profile-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.profile-username {
  color: var(--gray-400);
  font-size: 0.8125rem;
  margin-top: 1px;
}
.profile-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
  font-size: 0.8125rem;
  color: var(--gray-400);
}
.profile-meta > span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.profile-meta .material-icons-round {
  font-size: 14px;
}
.profile-bio {
  margin-top: 12px;
  color: var(--gray-600);
  line-height: 1.6;
  font-size: 0.875rem;
  padding-bottom: 16px;
}
.profile-skills-section {
  margin: 16px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-200);
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 6rem;
}
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .profile-meta {
    justify-content: center;
  }
  .profile-name-row {
    justify-content: center;
  }
}
</style>
```

- [ ] **Step 2: Verify in browser**

Run: `cd /Users/temporary/Developer/WorkWithUs/frontend && npm run dev`

Open `http://localhost:3000` in a browser. Navigate to a company profile and a student profile. Verify:
- Company profile shows: info grid (industry, website, location, projects), Projects tab, Applications tab (if owner), Reviews tab
- Student profile shows: education grid, skills section, Portfolio tab, Applications tab (if owner), Reviews tab
- Edit button opens the role-aware edit modal
- All tabs load their data correctly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProfilePage.vue
git commit -m "feat: rewrite ProfilePage as role-based orchestrator with sub-components"
```

---

### Task 18: ProjectDetailPage.vue Refactor

**Files:**
- Modify: `frontend/src/views/ProjectDetailPage.vue:7,22,162,257-258`

**Depends on:** Tasks 3, 5, 6 (ConfirmDialog, StatusBadge, EmptyState)

- [ ] **Step 1: Add imports for new components**

In `frontend/src/views/ProjectDetailPage.vue`, add the following imports after the existing imports at lines 169-174:

```javascript
import StatusBadge from '@/components/StatusBadge.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
```

Add the state for ConfirmDialog after line 192 (`const reviewedApps = ref(new Set())`):

```javascript
const showDeleteConfirm = ref(false)
```

- [ ] **Step 2: Replace status badges in template**

Replace the project status badge on line 7:
```html
<span class="badge" :class="statusBadge">{{ project.status }}</span>
```
with:
```html
<StatusBadge :status="project.status" size="md" />
```

Replace the application status badge at line 30:
```html
<span class="badge" :class="appStatusBadge(myApp.status)">{{ myApp.status }}</span>
```
with:
```html
<StatusBadge :status="myApp.status" size="md" />
```

Replace the application status badge at line 92:
```html
<span class="badge" :class="appStatusBadge(myApp.status)">{{ myApp.status }}</span>
```
with:
```html
<StatusBadge :status="myApp.status" />
```

Replace the application status badge at line 126:
```html
<span class="badge" :class="appStatusBadge(a.status)">{{ a.status }}</span>
```
with:
```html
<StatusBadge :status="a.status" />
```

- [ ] **Step 3: Replace empty state for applications list**

Replace line 162:
```html
<div v-else class="empty-state"><span class="material-icons-round">inbox</span><h3>No applications yet</h3></div>
```
with:
```html
<EmptyState v-else icon="inbox" title="No applications yet" subtitle="Applications will appear here when students apply" />
```

- [ ] **Step 4: Replace confirm() with ConfirmDialog**

Replace the delete button at line 22:
```html
<button class="btn btn-danger btn-sm" @click="deleteProject"><span class="material-icons-round">delete</span>Delete</button>
```
with:
```html
<button class="btn btn-danger btn-sm" @click="showDeleteConfirm = true"><span class="material-icons-round">delete</span>Delete</button>
```

Add the ConfirmDialog component just before the closing `</div>` of the main page (before line 164):
```html
<ConfirmDialog
  v-model="showDeleteConfirm"
  title="Delete Project"
  message="Delete this project permanently? This cannot be undone."
  @confirm="deleteProject"
/>
```

Replace the `deleteProject` function (lines 257-260):
```javascript
async function deleteProject() {
  if (!confirm('Delete this project permanently?')) return
  try { await projectsAPI.delete(project.value.id); toast.success('Deleted'); router.push('/projects') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```
with:
```javascript
async function deleteProject() {
  showDeleteConfirm.value = false
  try { await projectsAPI.delete(project.value.id); toast.success('Deleted'); router.push('/projects') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
```

- [ ] **Step 5: Clean up unused code**

Remove the `statusBadge` computed property (line 197) since it's replaced by StatusBadge component:
```javascript
const statusBadge = computed(() => ({ open: 'badge-success', in_progress: 'badge-warning', closed: 'badge-danger' }[project.value?.status]))
```

Remove the `appStatusBadge` function (lines 199-202) since it's replaced by StatusBadge component:
```javascript
function appStatusBadge(s) {
  return { pending: 'badge-info', accepted: 'badge-success', rejected: 'badge-danger', in_progress: 'badge-warning',
    submitted: 'badge-accent', revision_requested: 'badge-warning', approved: 'badge-success', completed: 'badge-teal' }[s] || 'badge-info'
}
```

- [ ] **Step 6: Verify in browser**

Open `http://localhost:3000` and navigate to a project detail page. Verify:
- Status badges use the new StatusBadge component with colored backgrounds
- Empty applications list shows the EmptyState component
- Clicking "Delete" opens the ConfirmDialog modal instead of browser `confirm()`
- Confirm dialog closes on Cancel and executes delete on Confirm

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/ProjectDetailPage.vue
git commit -m "refactor: use ConfirmDialog, StatusBadge, EmptyState in ProjectDetailPage"
```

---

## Verification Checklist

After all tasks are complete, verify the following end-to-end in the browser:

1. **Company profile** (`/profile/:id` for a company user):
   - Info grid shows industry, website (clickable), location, project count
   - Bio from company description
   - Projects tab lists company's projects with status badges
   - Applications tab (owner only) shows aggregated applications
   - Reviews tab shows reviews
   - Edit button opens modal with company-specific fields
   - Saving edit updates both user and company profile data

2. **Student profile** (`/profile/:id` for a student user):
   - Education grid shows university, major, graduation year, completed projects
   - Skills section with chips; owner can add/remove skills via dropdown
   - Portfolio tab shows enhanced cards with image area and ConfirmDialog on delete
   - Applications tab (owner only) shows applications with project titles
   - Reviews tab shows reviews
   - Edit button opens modal with student-specific fields

3. **Project detail page** (`/projects/:id`):
   - Status uses StatusBadge component
   - Application statuses use StatusBadge
   - Empty applications shows EmptyState
   - Delete uses ConfirmDialog instead of `confirm()`

4. **Dark mode**: Toggle dark mode and verify all new components use CSS variables correctly

5. **No regressions**: Existing functionality (auth, navigation, chat, notifications) is unaffected
