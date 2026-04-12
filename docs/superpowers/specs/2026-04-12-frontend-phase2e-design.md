# Frontend Phase 2E: Application Workflow Tracker

## Overview

Give students and companies a clear, auditable view of how each application has moved through the 8-stage workflow. Add a lightweight per-transition history to the backend, extract a reusable timeline component on the frontend, and consolidate workflow actions into a side drawer. Introduces the first dedicated Pinia store for applications.

**Scope:** 1 backend model + router change, 1 Aerich migration, 1 new Pinia store, 2 new Vue components, 4 modified Vue files, 3 new backend tests.

## 1. Backend: Status History

### Files
- Modify: `backend/src/applications/models.py`
- Modify: `backend/src/applications/router.py`
- Create: `backend/migrations/models/<next>_add_status_history.py` (Aerich-generated)
- Modify: `backend/src/tests/test_features.py` (or create `backend/src/tests/test_applications_history.py`)

### Model change

`Application` gains:
```python
status_history = fields.JSONField(default=list)
```
Stored as a JSON array of entries.

### Entry shape

```python
class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    actor_id: Optional[int] = None
    actor_name: str
    note: Optional[str] = None
```

- `status` — one of the 8 ApplicationStatus enum values
- `timestamp` — ISO 8601 UTC
- `actor_id` — null only for system/backfill entries
- `actor_name` — denormalized at write-time from the actor's `full_name` (so historical records don't break when a user renames)
- `note` — populated when transitioning to `submitted` (submission_note) or `revision_requested` (revision_note); otherwise null

### Schema change

`ApplicationResponse` gains:
```python
status_history: list[StatusHistoryEntry] = []
```

### Transition logic

Add a helper in `router.py`:
```python
def _append_history(app, status: str, actor: User, note: Optional[str] = None) -> list[dict]:
    entry = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "actor_id": actor.id,
        "actor_name": actor.full_name,
        "note": note,
    }
    history = list(app.status_history or [])
    history.append(entry)
    return history
```

Call sites:
- **`POST /applications/`** (create) — after `Application.create(...)`, set `app.status_history = _append_history(app, "pending", current_user, None)` and `await app.save()`.
- **`PUT /applications/{id}/status`** — after status validation, before the existing `app.save()`, set `app.status_history = _append_history(app, new_status, current_user, note)` where `note = submission_note or revision_note or None` (whichever is relevant to the target status).

### Aerich migration

**Schema part:** Add `status_history` JSONB column, default `[]`, not null.

**Data backfill (Python upgrade function body):**
```python
async def upgrade(db) -> str:
    return """
    ALTER TABLE applications ADD COLUMN status_history JSONB NOT NULL DEFAULT '[]'::jsonb;
    """
```
Then a second migration (or a second statement in the same migration) runs the backfill logic in Python using Tortoise. For each application:
- Fetch `applicant.full_name`.
- Build initial `pending` entry: `{status: "pending", timestamp: created_at.isoformat(), actor_id: applicant_id, actor_name: applicant.full_name, note: null}`.
- If `status != "pending"`, append a second entry: `{status: current_status, timestamp: updated_at.isoformat(), actor_id: null, actor_name: "System (backfill)", note: submission_note or revision_note or null}`.
- Write the array to `status_history` and save.

This is implemented as a standalone backfill script at `backend/scripts/backfill_status_history.py` rather than inside the Aerich migration (Aerich SQL migrations don't easily handle complex Python per-row logic). The migration adds the column; the script populates it. Deployment: run `aerich upgrade` then `python scripts/backfill_status_history.py`.

### Tests

Three new tests (added to existing `test_features.py` or new `test_applications_history.py`):

1. **`test_create_application_initializes_history`** — Student applies to a project; response includes `status_history` with exactly one entry: `status="pending"`, `actor_id=student_id`, `note is None`.
2. **`test_status_transition_appends_history`** — Company accepts a pending app; response's `status_history` has 2 entries (pending then accepted); the accepted entry has `actor_id=company_id` and `note is None`. Then student transitions to `in_progress`, and a third entry appears with `actor_id=student_id`.
3. **`test_submission_note_captured_in_history`** — Student submits work with `submission_note="v1 ready"`; the appended history entry has `status="submitted"` and `note="v1 ready"`. Symmetric test for `revision_requested` + `revision_note`.

Backfill is not unit-tested — it's a one-time migration script verified manually on a dev database.

## 2. Frontend: Pinia Applications Store

### File
- Create: `frontend/src/stores/applications.js`

### Implementation

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { applicationsAPI } from '@/api'

export const useApplicationsStore = defineStore('applications', () => {
  const myApps = ref([])
  const byProject = ref({})     // { [projectId]: Application[] }
  const loading = ref(false)
  const error = ref(null)

  async function fetchMy() {
    loading.value = true
    try {
      const { data } = await applicationsAPI.my()
      myApps.value = data
    } catch (err) {
      error.value = err
      console.error('fetchMy failed', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchByProject(projectId) {
    loading.value = true
    try {
      const { data } = await applicationsAPI.byProject(projectId)
      byProject.value[projectId] = data
    } catch (err) {
      error.value = err
      console.error('fetchByProject failed', err)
    } finally {
      loading.value = false
    }
  }

  async function apply(payload) {
    const { data } = await applicationsAPI.apply(payload)
    myApps.value.unshift(data)
    return data
  }

  async function updateStatus(id, payload) {
    const { data } = await applicationsAPI.updateStatus(id, payload)
    const i = myApps.value.findIndex(a => a.id === id)
    if (i !== -1) myApps.value[i] = data
    for (const pid in byProject.value) {
      const j = byProject.value[pid].findIndex(a => a.id === id)
      if (j !== -1) byProject.value[pid][j] = data
    }
    return data
  }

  return { myApps, byProject, loading, error, fetchMy, fetchByProject, apply, updateStatus }
})
```

### Design notes

- In-place patching on `updateStatus` lets open drawers reflect changes reactively without re-fetching.
- `byProject` keyed by projectId avoids redundant refetches when switching between tabs on ProjectDetailPage.
- Errors are logged and stored on `error` — consistent with the Phase 2B store pattern.

## 3. Frontend: ApplicationTimeline Component

### File
- Create: `frontend/src/components/ApplicationTimeline.vue`

### Props
- `history: Array` (required) — shape matches backend `StatusHistoryEntry` list.

### Layout

Vertical list. Each entry is a row with:
- Left gutter: 14×14 dot + `2px` connector line between dots.
- Right content: status label + timestamp (right-aligned), actor line, optional note blockquote.

### Helper functions (inside `<script setup>`)

```js
const STATUS_LABELS = {
  pending: 'Pending',
  accepted: 'Accepted',
  rejected: 'Rejected',
  in_progress: 'In Progress',
  submitted: 'Submitted',
  revision_requested: 'Revision Requested',
  approved: 'Approved',
  completed: 'Completed',
}

const STATUS_COLORS = {
  pending: 'var(--gray-400)',
  accepted: 'var(--success)',
  rejected: 'var(--danger)',
  in_progress: 'var(--info)',
  submitted: 'var(--accent)',
  revision_requested: 'var(--warning)',
  approved: 'var(--success)',
  completed: 'var(--success)',
}

function formatTimestamp(iso) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  }).format(new Date(iso))
}
```

### Visual rules

- Latest entry's dot uses `STATUS_COLORS[entry.status]`; prior dots use `var(--gray-300)`.
- Connector line runs between dots, hidden on the last entry.
- Timestamp format: `Apr 10, 2026, 2:34 PM` (uses `Intl.DateTimeFormat` default with the options above).
- Empty `history` array: render nothing. The consumer (drawer) decides what to show.

### Scoped styles

Uses existing CSS variables: `--gray-200`, `--gray-300`, `--gray-500`, `--gray-700`, plus the status palette vars listed above.

## 4. Frontend: ApplicationDetailDrawer Component

### File
- Create: `frontend/src/components/ApplicationDetailDrawer.vue`

### Props
- `application: Object | null` — the application to display. `null` closes the drawer.
- `viewAs: 'student' | 'company'` — controls which action buttons render.

### Emits
- `close` — user clicked the backdrop, pressed ESC, or clicked the × button.
- `action-complete` — a status change succeeded (parent may refetch lists or close the drawer).

### Layout (420px wide right-side drawer)

```
┌───────────────────────────────┐
│ Application details        ×  │
├───────────────────────────────┤
│  Project title                │
│  [StatusBadge current]        │
│                               │
│  Cover letter (if present):   │
│  "..."                        │
│                               │
│  Timeline                     │
│  <ApplicationTimeline />      │
├───────────────────────────────┤
│  [ Action buttons ]           │  ← sticky footer, border-top
└───────────────────────────────┘
```

### Backdrop + animation

- Backdrop: full-viewport `rgba(0,0,0,0.4)`.
- Drawer enters via `transform: translateX(100%) → 0` over 200ms ease.
- Teleported to `body` so it escapes parent `overflow:hidden`.
- ESC key closes.
- Clicking the backdrop closes.

### Action buttons (by `viewAs` + current status)

| viewAs | status | Buttons |
|--------|--------|---------|
| student | accepted | Start Working |
| student | in_progress | Submit Work |
| student | revision_requested | Submit Work |
| company | pending | Accept, Reject |
| company | submitted | Approve, Request Revision |
| company | approved | Mark Completed |
| (any) | terminal (rejected/completed) | none (drawer is read-only) |

### Note-prompt flow

For **Submit Work** and **Request Revision** (both require a note), clicking the button reveals an inline `<textarea>` above the footer with Cancel / Confirm. Confirm calls:
```js
await store.updateStatus(app.id, { status: 'submitted', submission_note: noteText })
// or
await store.updateStatus(app.id, { status: 'revision_requested', revision_note: noteText })
```
Other action buttons call `store.updateStatus(app.id, { status: <target> })` directly, no prompt.

After a successful action, the drawer stays open — the store's in-place patch re-renders the timeline with the new entry reactively. `emit('action-complete')` fires so parent can refresh its list if needed.

### Error handling

If `store.updateStatus` throws, show an inline error message below the buttons: `"Could not update status — please try again."` in `var(--danger)`. Do not close the drawer.

### Styling notes

- Uses existing `var(--radius-lg)`, shadows, and gray scale.
- Footer is `position: sticky; bottom: 0` with white background and `border-top: 1px solid var(--gray-200)`.
- Implemented inline (no dependence on `BaseModal`) to avoid coupling.

## 5. Page Integrations

### `frontend/src/views/MyApplicationsPage.vue` (modify)

Current state: list of applications with inline workflow-bar stepper + inline action buttons.

Changes:
- Remove the inline workflow-bar stepper and inline action buttons.
- Each card becomes a summary:
  - Project title (links to project detail page).
  - Latest `StatusBadge`.
  - Line: `Latest: {STATUS_LABELS[latest.status]} · {formatTimestamp(latest.timestamp)}` (derived from `application.status_history[application.status_history.length - 1]`).
  - Bottom-right: `View details →` affordance.
- Whole card clickable → sets `selected.value = application`, opens `<ApplicationDetailDrawer :application="selected" viewAs="student" @close="selected = null" />`.
- Replace local `applications` ref with `store.myApps`. Call `store.fetchMy()` in `onMounted`.
- Loading state uses existing `<SkeletonBlock>` cards.

### `frontend/src/views/ProjectDetailPage.vue` (modify)

Current state: owner sees a list of applications with inline action buttons; student sees their own application with inline status + buttons.

Changes:
- Owner applications list: each row becomes a clickable summary (applicant name, StatusBadge, latest event timestamp). Click opens `<ApplicationDetailDrawer :application="selected" viewAs="company" @close="selected = null" />`.
- Remove the inline owner action buttons (Accept/Reject/Approve/etc.).
- Student's own application section: keep the current inline status summary (StatusBadge + latest event) for at-a-glance visibility, but remove the inline action buttons. Add a `View full history & actions` button that opens `<ApplicationDetailDrawer :application="myApp" viewAs="student" />`.
- Replace direct `applicationsAPI` calls with `store.fetchByProject(projectId)` and `store.updateStatus(...)`.

### `frontend/src/components/dashboard/DashboardStudentSection.vue` (modify)

- Swap the direct `applicationsAPI.my()` call for `store.fetchMy()`.
- Read from `store.myApps` instead of the local `allApps` ref.
- Preserve the existing slice-to-5 display and stats computation.
- No UI changes.

### `frontend/src/components/dashboard/DashboardCompanySection.vue` (modify)

- Swap the direct `applicationsAPI.byProject(pid)` calls for `store.fetchByProject(pid)`.
- Read from `store.byProject[pid]`.
- Preserve the existing aggregation logic.
- No UI changes.

## Files Summary

| Action | File | Changes |
|--------|------|---------|
| Modify | `backend/src/applications/models.py` | Add `status_history` JSONField |
| Modify | `backend/src/applications/router.py` | `_append_history` helper, updated schemas, append on create/transition |
| Create | `backend/migrations/models/<next>_add_status_history.py` | Aerich schema migration (column only) |
| Create | `backend/scripts/backfill_status_history.py` | One-time backfill script for existing rows |
| Modify | `backend/src/tests/test_features.py` | 3 new tests for history tracking |
| Create | `frontend/src/stores/applications.js` | Pinia store (Composition API style) |
| Create | `frontend/src/components/ApplicationTimeline.vue` | Vertical timeline (presentational) |
| Create | `frontend/src/components/ApplicationDetailDrawer.vue` | Side drawer with timeline + actions |
| Modify | `frontend/src/views/MyApplicationsPage.vue` | Summary cards, drawer integration, store usage |
| Modify | `frontend/src/views/ProjectDetailPage.vue` | Summary list, drawer integration, store usage |
| Modify | `frontend/src/components/dashboard/DashboardStudentSection.vue` | Use store instead of direct API |
| Modify | `frontend/src/components/dashboard/DashboardCompanySection.vue` | Use store instead of direct API |
