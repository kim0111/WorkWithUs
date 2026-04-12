# Frontend Phase 2E: Application Workflow Tracker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-transition status history to applications and surface it in a reusable side-drawer timeline across the student and company workflows.

**Architecture:** Backend stores a `status_history` JSON array on each Application, appended whenever status changes. Frontend introduces a first dedicated Pinia applications store, a presentational `<ApplicationTimeline>` component, and an `<ApplicationDetailDrawer>` that consolidates workflow actions. Two pages and two dashboard sections are refactored to consume the store + drawer.

**Tech Stack:** FastAPI, Tortoise ORM, Aerich (schema migrations), Pydantic v2, Vue 3 Composition API, Pinia, scoped CSS with CSS variables.

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `backend/src/applications/models.py` | Add `status_history` JSONField |
| Modify | `backend/src/applications/router.py` | `StatusHistoryEntry` schema, `_append_history` helper, integration into apply + update_status |
| Create | `backend/src/tests/test_applications_history.py` | TDD tests for history tracking |
| Create | `backend/migrations/models/<aerich-generated>.py` | Schema migration: add `status_history` column |
| Create | `backend/scripts/backfill_status_history.py` | One-time script to populate `status_history` on existing rows |
| Create | `frontend/src/stores/applications.js` | Pinia store (Composition API style) |
| Create | `frontend/src/components/ApplicationTimeline.vue` | Presentational vertical timeline |
| Create | `frontend/src/components/ApplicationDetailDrawer.vue` | Right-side drawer with timeline + action buttons |
| Modify | `frontend/src/views/MyApplicationsPage.vue` | Summary cards, drawer integration, store usage |
| Modify | `frontend/src/views/ProjectDetailPage.vue` | Applications list + my-app section refactor to use drawer + store |
| Modify | `frontend/src/components/dashboard/DashboardStudentSection.vue` | Read from store instead of direct API |
| Modify | `frontend/src/components/dashboard/DashboardCompanySection.vue` | Read from store instead of direct API |

---

### Task 1: Backend — status_history field, schema, helper, and endpoint integration (TDD)

**Files:**
- Modify: `backend/src/applications/models.py`
- Modify: `backend/src/applications/router.py`
- Create: `backend/src/tests/test_applications_history.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/src/tests/test_applications_history.py`:

```python
import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


async def _create_project(client, company_token, title="Demo Project"):
    r = await client.post("/api/v1/projects/", json={
        "title": title, "description": "A demo project for history tests",
    }, headers=auth(company_token))
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_application_initializes_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """Applying should seed status_history with exactly one 'pending' entry by the applicant."""
    project_id = await _create_project(client, company_token)

    r = await client.post("/api/v1/applications/", json={
        "project_id": project_id, "cover_letter": "please pick me",
    }, headers=auth(student_token))
    assert r.status_code == 201
    body = r.json()

    assert "status_history" in body
    assert len(body["status_history"]) == 1
    entry = body["status_history"][0]
    assert entry["status"] == "pending"
    assert entry["actor_id"] is not None
    assert entry["actor_name"]  # non-empty
    assert entry["note"] is None


@pytest.mark.asyncio
async def test_status_transition_appends_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """Each transition should append one new entry with the correct actor."""
    project_id = await _create_project(client, company_token)

    apply_r = await client.post("/api/v1/applications/", json={
        "project_id": project_id,
    }, headers=auth(student_token))
    app_id = apply_r.json()["id"]

    # Company accepts
    accept_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(company_token),
    )
    assert accept_r.status_code == 200
    body = accept_r.json()
    assert len(body["status_history"]) == 2
    assert body["status_history"][1]["status"] == "accepted"
    assert body["status_history"][1]["note"] is None

    # Student starts working
    start_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "in_progress"}, headers=auth(student_token),
    )
    assert start_r.status_code == 200
    body = start_r.json()
    assert len(body["status_history"]) == 3
    assert body["status_history"][2]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_submission_note_captured_in_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """submission_note and revision_note should be captured per-transition in history."""
    project_id = await _create_project(client, company_token)

    apply_r = await client.post("/api/v1/applications/", json={
        "project_id": project_id,
    }, headers=auth(student_token))
    app_id = apply_r.json()["id"]

    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "accepted"}, headers=auth(company_token))
    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "in_progress"}, headers=auth(student_token))

    # Submit with a note
    submit_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "submitted", "note": "v1 ready for review"},
        headers=auth(student_token),
    )
    assert submit_r.status_code == 200
    body = submit_r.json()
    submitted_entry = body["status_history"][-1]
    assert submitted_entry["status"] == "submitted"
    assert submitted_entry["note"] == "v1 ready for review"

    # Request revision with a note
    rev_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "revision_requested", "note": "fix the README"},
        headers=auth(company_token),
    )
    assert rev_r.status_code == 200
    body = rev_r.json()
    rev_entry = body["status_history"][-1]
    assert rev_entry["status"] == "revision_requested"
    assert rev_entry["note"] == "fix the README"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/backend && python3 -m pytest src/tests/test_applications_history.py -v
```
Expected: All 3 tests FAIL (KeyError on `status_history` — the field doesn't exist yet).

- [ ] **Step 3: Add `status_history` field to the Application model**

In `backend/src/applications/models.py`, add a single line to the `Application` class after the `updated_at` field (line 25). The final model should look like:

```python
import enum
from tortoise import fields, models


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_requested = "revision_requested"
    approved = "approved"
    completed = "completed"


class Application(models.Model):
    id = fields.IntField(primary_key=True)
    project = fields.ForeignKeyField("models.Project", related_name="applications", on_delete=fields.CASCADE)
    applicant = fields.ForeignKeyField("models.User", related_name="applications", on_delete=fields.CASCADE)
    cover_letter = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=ApplicationStatus, default=ApplicationStatus.pending)
    submission_note = fields.TextField(null=True)
    revision_note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    status_history = fields.JSONField(default=list)

    class Meta:
        table = "applications"
        unique_together = (("project", "applicant"),)
```

- [ ] **Step 4: Add `StatusHistoryEntry` schema and integrate `status_history` into responses**

In `backend/src/applications/router.py`:

Replace the existing schema section (lines 13–36) with:

```python
# -- Schemas --

class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    actor_id: Optional[int] = None
    actor_name: str
    note: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
```

- [ ] **Step 5: Add the `_append_history` helper**

In `backend/src/applications/router.py`, after the `VALID_TRANSITIONS` dict (line 48) and before the `router = APIRouter(...)` line, insert:

```python
def _append_history(app: Application, status: str, actor: User, note: Optional[str] = None) -> list[dict]:
    entry = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "actor_id": actor.id,
        "actor_name": actor.full_name or actor.username,
        "note": note,
    }
    history = list(app.status_history or [])
    history.append(entry)
    return history
```

- [ ] **Step 6: Seed history on application creation**

In `backend/src/applications/router.py`, modify the `apply` endpoint. Replace the block (lines 78–80):

```python
    application = await Application.create(
        project_id=data.project_id, applicant_id=current_user.id, cover_letter=data.cover_letter,
    )
```

with:

```python
    application = await Application.create(
        project_id=data.project_id, applicant_id=current_user.id, cover_letter=data.cover_letter,
    )
    application.status_history = _append_history(application, "pending", current_user, None)
    await application.save()
```

- [ ] **Step 7: Append history on every status transition**

In `backend/src/applications/router.py`, modify the `update_status` endpoint. Replace the block (lines 122–127):

```python
    application.status = data.status
    if data.status == ApplicationStatus.submitted and data.note:
        application.submission_note = data.note
    if data.status == ApplicationStatus.revision_requested and data.note:
        application.revision_note = data.note
    await application.save()
```

with:

```python
    application.status = data.status
    if data.status == ApplicationStatus.submitted and data.note:
        application.submission_note = data.note
    if data.status == ApplicationStatus.revision_requested and data.note:
        application.revision_note = data.note
    application.status_history = _append_history(
        application, data.status.value, current_user, data.note
    )
    await application.save()
```

- [ ] **Step 8: Run the new tests to verify they pass**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/backend && python3 -m pytest src/tests/test_applications_history.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 9: Run the full backend test suite to check for regressions**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/backend && python3 -m pytest src/tests/ -v
```
Expected: All tests pass (existing 65 + 3 new = 68).

- [ ] **Step 10: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add backend/src/applications/models.py backend/src/applications/router.py backend/src/tests/test_applications_history.py && \
  git commit -m "feat: add status_history tracking to applications

Append an entry on application creation and on every status transition,
capturing the acting user and any transition note. Status history is
exposed on ApplicationResponse." 
```

---

### Task 2: Backend — Aerich migration and backfill script

**Files:**
- Create: `backend/migrations/models/<aerich-generated>.py`
- Create: `backend/scripts/backfill_status_history.py`

- [ ] **Step 1: Generate the Aerich migration**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/backend && aerich migrate --name "add_status_history"
```
Expected: a new file is created under `backend/migrations/models/`, with a name like `1_YYYYMMDDHHMMSS_add_status_history.py`. It contains SQL that adds the `status_history` JSON column with default `[]`.

If `aerich` is not installed locally, install: `pip install aerich`. The migration does not need to be applied locally (tests use in-memory SQLite that regenerates schema).

- [ ] **Step 2: Create the backfill script**

Create `backend/scripts/backfill_status_history.py`:

```python
"""One-time backfill script for Application.status_history.

Populates status_history for existing applications using this rule:
  - Always: 1 entry at created_at with status="pending",
    actor = the applicant, note = None.
  - If current status != "pending": 1 additional entry at updated_at
    with the current status, actor_id = None, actor_name = "System (backfill)",
    and note = submission_note or revision_note or None.

Usage (from the backend/ directory):

    python3 scripts/backfill_status_history.py
"""
import asyncio
from tortoise import Tortoise
from src.database.postgres import TORTOISE_ORM
from src.applications.models import Application
from src.users.models import User


async def backfill():
    await Tortoise.init(config=TORTOISE_ORM)

    applications = await Application.all()
    updated = 0
    for app in applications:
        if app.status_history:
            continue  # skip rows that already have history
        applicant = await User.filter(id=app.applicant_id).first()
        actor_name = (applicant.full_name or applicant.username) if applicant else "Unknown"
        history = [{
            "status": "pending",
            "timestamp": app.created_at.isoformat(),
            "actor_id": app.applicant_id,
            "actor_name": actor_name,
            "note": None,
        }]
        if app.status.value != "pending":
            history.append({
                "status": app.status.value,
                "timestamp": app.updated_at.isoformat(),
                "actor_id": None,
                "actor_name": "System (backfill)",
                "note": app.submission_note or app.revision_note or None,
            })
        app.status_history = history
        await app.save()
        updated += 1

    print(f"Backfilled status_history for {updated} application(s)")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(backfill())
```

- [ ] **Step 3: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add backend/migrations/models/ backend/scripts/backfill_status_history.py && \
  git commit -m "chore: aerich migration + backfill script for status_history

Adds the status_history JSON column via Aerich and a standalone Python
script that populates it for existing applications (pending-at-created
plus a synthetic current-status entry when applicable)."
```

---

### Task 3: Frontend — Applications Pinia store

**Files:**
- Create: `frontend/src/stores/applications.js`

- [ ] **Step 1: Create the store**

Create `frontend/src/stores/applications.js`:

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { applicationsAPI } from '@/api'

export const useApplicationsStore = defineStore('applications', () => {
  const myApps = ref([])
  const byProject = ref({})
  const loading = ref(false)
  const error = ref(null)

  async function fetchMy() {
    loading.value = true
    try {
      const { data } = await applicationsAPI.my()
      myApps.value = data
    } catch (err) {
      error.value = err
      console.error('applications.fetchMy failed', err)
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
      console.error('applications.fetchByProject failed', err)
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

- [ ] **Step 2: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/stores/applications.js && \
  git commit -m "feat: add Pinia applications store with in-place updateStatus patching"
```

---

### Task 4: Frontend — `<ApplicationTimeline>` component

**Files:**
- Create: `frontend/src/components/ApplicationTimeline.vue`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/ApplicationTimeline.vue`:

```vue
<template>
  <ol v-if="history?.length" class="timeline">
    <li
      v-for="(entry, i) in history"
      :key="i"
      class="tl-item"
      :class="{ 'tl-last': i === history.length - 1 }"
    >
      <span
        class="tl-dot"
        :style="{ backgroundColor: dotColor(entry.status, i === history.length - 1) }"
      ></span>
      <div class="tl-content">
        <div class="tl-row">
          <span class="tl-status">{{ STATUS_LABELS[entry.status] || entry.status }}</span>
          <span class="tl-time">{{ formatTimestamp(entry.timestamp) }}</span>
        </div>
        <div class="tl-actor">by {{ entry.actor_name }}</div>
        <blockquote v-if="entry.note" class="tl-note">{{ entry.note }}</blockquote>
      </div>
    </li>
  </ol>
</template>

<script setup>
defineProps({
  history: { type: Array, required: true },
})

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

function dotColor(status, isLast) {
  return isLast ? (STATUS_COLORS[status] || 'var(--gray-400)') : 'var(--gray-300)'
}

function formatTimestamp(iso) {
  if (!iso) return ''
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}
</script>

<style scoped>
.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
  position: relative;
}
.tl-item {
  position: relative;
  padding-left: 28px;
  padding-bottom: 20px;
}
.tl-item:not(.tl-last)::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 16px;
  bottom: 0;
  width: 2px;
  background: var(--gray-200);
}
.tl-dot {
  position: absolute;
  left: 0;
  top: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--white);
  box-shadow: 0 0 0 1px var(--gray-200);
}
.tl-content { display: flex; flex-direction: column; gap: 2px; }
.tl-row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.tl-status { font-size: .875rem; font-weight: 600; color: var(--gray-900); }
.tl-time { font-size: .75rem; color: var(--gray-500); white-space: nowrap; }
.tl-actor { font-size: .8125rem; color: var(--gray-500); }
.tl-note {
  margin: 6px 0 0;
  padding: 6px 10px;
  border-left: 2px solid var(--gray-200);
  background: var(--gray-50);
  color: var(--gray-700);
  font-size: .8125rem;
  font-style: italic;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/components/ApplicationTimeline.vue && \
  git commit -m "feat: add ApplicationTimeline component for status history"
```

---

### Task 5: Frontend — `<ApplicationDetailDrawer>` component

**Files:**
- Create: `frontend/src/components/ApplicationDetailDrawer.vue`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/ApplicationDetailDrawer.vue`:

```vue
<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="application" class="drawer-backdrop" @click.self="close" @keydown.esc="close" tabindex="0">
        <aside class="drawer" role="dialog" aria-label="Application details">
          <header class="drawer-head">
            <h3>Application details</h3>
            <button class="drawer-close" @click="close" aria-label="Close">
              <span class="material-icons-round">close</span>
            </button>
          </header>

          <div class="drawer-body">
            <div class="app-summary">
              <div class="summary-top">
                <div class="summary-title">Project #{{ application.project_id }}</div>
                <StatusBadge :status="application.status" size="md" />
              </div>
              <p v-if="application.cover_letter" class="cover-letter">
                <strong>Cover letter:</strong> {{ application.cover_letter }}
              </p>
            </div>

            <h4 class="section-heading">Timeline</h4>
            <ApplicationTimeline :history="application.status_history || []" />
            <p v-if="!application.status_history?.length" class="no-history">
              No history recorded yet — future changes will appear here.
            </p>

            <div v-if="noteFor" class="note-input">
              <textarea
                class="input"
                v-model="noteText"
                rows="3"
                :placeholder="noteFor === 'submitted' ? 'Submission note...' : 'Revision note...'"
              ></textarea>
              <div class="note-actions">
                <button class="btn btn-ghost btn-sm" @click="cancelNote">Cancel</button>
                <button class="btn btn-primary btn-sm" @click="confirmNote" :disabled="busy">
                  {{ busy ? 'Saving...' : 'Confirm' }}
                </button>
              </div>
            </div>

            <p v-if="errorMsg" class="drawer-error">{{ errorMsg }}</p>
          </div>

          <footer v-if="actionButtons.length && !noteFor" class="drawer-foot">
            <button
              v-for="btn in actionButtons"
              :key="btn.status"
              :class="btn.class"
              :disabled="busy"
              @click="onAction(btn)"
            >
              <span v-if="btn.icon" class="material-icons-round">{{ btn.icon }}</span>
              {{ btn.label }}
            </button>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'
import ApplicationTimeline from '@/components/ApplicationTimeline.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const props = defineProps({
  application: { type: Object, default: null },
  viewAs: { type: String, required: true, validator: v => ['student', 'company'].includes(v) },
})
const emit = defineEmits(['close', 'action-complete'])

const store = useApplicationsStore()
const busy = ref(false)
const errorMsg = ref('')
const noteFor = ref(null)   // 'submitted' | 'revision_requested' | null
const noteText = ref('')

function close() {
  if (busy.value) return
  errorMsg.value = ''
  noteFor.value = null
  noteText.value = ''
  emit('close')
}

const actionButtons = computed(() => {
  if (!props.application) return []
  const s = props.application.status
  if (props.viewAs === 'student') {
    if (s === 'accepted') return [{ status: 'in_progress', label: 'Start Working', icon: 'play_arrow', class: 'btn btn-primary btn-sm' }]
    if (s === 'in_progress' || s === 'revision_requested') return [{ status: 'submitted', label: 'Submit Work', icon: 'send', class: 'btn btn-primary btn-sm', requiresNote: true }]
    return []
  }
  if (props.viewAs === 'company') {
    if (s === 'pending') return [
      { status: 'accepted', label: 'Accept', icon: 'check', class: 'btn btn-primary btn-sm' },
      { status: 'rejected', label: 'Reject', icon: 'close', class: 'btn btn-danger btn-sm' },
    ]
    if (s === 'submitted') return [
      { status: 'approved', label: 'Approve', icon: 'check_circle', class: 'btn btn-primary btn-sm' },
      { status: 'revision_requested', label: 'Request Revision', icon: 'edit_note', class: 'btn btn-outline btn-sm', requiresNote: true },
    ]
    if (s === 'approved') return [{ status: 'completed', label: 'Mark Completed', icon: 'task_alt', class: 'btn btn-primary btn-sm' }]
  }
  return []
})

function onAction(btn) {
  errorMsg.value = ''
  if (btn.requiresNote) {
    noteFor.value = btn.status
    noteText.value = ''
    return
  }
  runUpdate(btn.status, null)
}

function cancelNote() {
  noteFor.value = null
  noteText.value = ''
}

async function confirmNote() {
  if (!noteText.value.trim()) {
    errorMsg.value = 'Please enter a note before confirming.'
    return
  }
  await runUpdate(noteFor.value, noteText.value.trim())
}

async function runUpdate(status, note) {
  busy.value = true
  errorMsg.value = ''
  try {
    await store.updateStatus(props.application.id, { status, note })
    noteFor.value = null
    noteText.value = ''
    emit('action-complete')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Could not update status — please try again.'
  } finally {
    busy.value = false
  }
}

function onEsc(e) { if (e.key === 'Escape') close() }
onMounted(() => window.addEventListener('keydown', onEsc))
onUnmounted(() => window.removeEventListener('keydown', onEsc))

watch(() => props.application, (val) => {
  if (!val) {
    errorMsg.value = ''
    noteFor.value = null
    noteText.value = ''
  }
})
</script>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}
.drawer {
  width: 420px;
  max-width: 100vw;
  height: 100%;
  background: var(--white);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--gray-200);
}
.drawer-head h3 { font-size: 1rem; margin: 0; }
.drawer-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--gray-500);
  padding: 4px;
  display: flex;
  align-items: center;
}
.drawer-close:hover { color: var(--gray-900); }
.drawer-body {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
}
.app-summary {
  padding: 12px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}
.summary-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.summary-title { font-weight: 600; font-size: .9375rem; }
.cover-letter { font-size: .8125rem; color: var(--gray-700); line-height: 1.5; margin: 0; }
.section-heading { font-size: .875rem; font-weight: 600; margin: 0 0 10px; color: var(--gray-700); }
.no-history { font-size: .8125rem; color: var(--gray-500); padding: 8px 0; }
.note-input {
  margin-top: 16px;
  padding: 12px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.note-actions { display: flex; justify-content: flex-end; gap: 8px; }
.drawer-error {
  margin-top: 10px;
  padding: 8px 10px;
  font-size: .8125rem;
  color: var(--danger);
  background: var(--danger-light);
  border-radius: var(--radius-md);
}
.drawer-foot {
  padding: 12px 20px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  background: var(--white);
}

.drawer-fade-enter-active .drawer { transition: transform .2s ease; }
.drawer-fade-leave-active .drawer { transition: transform .2s ease; }
.drawer-fade-enter-from .drawer { transform: translateX(100%); }
.drawer-fade-leave-to .drawer { transform: translateX(100%); }
.drawer-fade-enter-active { transition: opacity .2s ease; }
.drawer-fade-leave-active { transition: opacity .2s ease; }
.drawer-fade-enter-from, .drawer-fade-leave-to { opacity: 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/components/ApplicationDetailDrawer.vue && \
  git commit -m "feat: add ApplicationDetailDrawer with timeline, action buttons, note prompts"
```

---

### Task 6: Frontend — MyApplicationsPage refactor

**Files:**
- Modify: `frontend/src/views/MyApplicationsPage.vue`

This task fully replaces the existing file. The new page shows summary cards and opens the drawer on click; inline stepper and action buttons are removed (they live in the drawer).

- [ ] **Step 1: Replace `frontend/src/views/MyApplicationsPage.vue` with the new version**

```vue
<template>
  <div class="page container">
    <header class="page-header"><h1>My Applications</h1></header>
    <div v-if="store.loading" class="apps-list">
      <div v-for="n in 4" :key="n" class="app-card card">
        <SkeletonBlock height="18px" width="60%" />
        <div style="margin-top: 10px;"><SkeletonBlock height="12px" width="40%" /></div>
      </div>
    </div>
    <div v-else-if="store.myApps.length" class="apps-list">
      <button
        v-for="a in store.myApps"
        :key="a.id"
        type="button"
        class="app-card card"
        @click="selected = a"
      >
        <div class="app-header">
          <div class="app-project-link">
            <span class="material-icons-round">folder</span>
            {{ projectTitles[a.project_id] || `Project #${a.project_id}` }}
          </div>
          <StatusBadge :status="a.status" />
        </div>
        <p v-if="a.cover_letter" class="app-letter">{{ a.cover_letter }}</p>
        <div class="app-footer">
          <span class="text-muted">{{ latestSummary(a) }}</span>
          <span class="view-details">View details <span class="material-icons-round">chevron_right</span></span>
        </div>
      </button>
    </div>
    <EmptyState
      v-else
      icon="send"
      title="No applications yet"
      subtitle="Browse projects and apply to get started"
      actionText="Browse Projects"
      actionTo="/projects"
    />

    <ApplicationDetailDrawer
      :application="selected"
      view-as="student"
      @close="selected = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
import ApplicationDetailDrawer from '@/components/ApplicationDetailDrawer.vue'

const store = useApplicationsStore()
const selected = ref(null)
const projectTitles = ref({})

const STATUS_LABELS = {
  pending: 'Pending', accepted: 'Accepted', rejected: 'Rejected',
  in_progress: 'In Progress', submitted: 'Submitted',
  revision_requested: 'Revision Requested', approved: 'Approved', completed: 'Completed',
}

function latestSummary(app) {
  const hist = app.status_history || []
  if (!hist.length) return `Applied ${fmtDate(app.created_at)}`
  const latest = hist[hist.length - 1]
  return `Latest: ${STATUS_LABELS[latest.status] || latest.status} · ${fmtDate(latest.timestamp)}`
}

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

onMounted(async () => {
  await store.fetchMy()
  // Resolve project titles for each application in parallel
  const ids = [...new Set(store.myApps.map(a => a.project_id))]
  const results = await Promise.allSettled(ids.map(id => projectsAPI.get(id)))
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') projectTitles.value[ids[i]] = r.value.data.title
  })
})
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.apps-list { display: flex; flex-direction: column; gap: 12px; }
.app-card {
  padding: 16px;
  text-align: left;
  width: 100%;
  border: 1px solid var(--gray-200);
  background: var(--white);
  cursor: pointer;
  transition: all .15s ease;
  border-radius: var(--radius-lg);
}
.app-card:hover { border-color: var(--gray-300); box-shadow: var(--shadow-sm); }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.app-project-link { display: flex; align-items: center; gap: 6px; color: var(--gray-900); font-weight: 500; font-size: .9375rem; }
.app-project-link .material-icons-round { color: var(--accent); font-size: 18px; }
.app-letter { color: var(--gray-600); font-size: .8125rem; margin-bottom: 10px; line-height: 1.5; }
.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
}
.text-muted { color: var(--gray-500); font-size: .8125rem; }
.view-details {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--accent);
  font-size: .8125rem;
  font-weight: 500;
}
.view-details .material-icons-round { font-size: 16px; }
</style>
```

- [ ] **Step 2: Run the frontend build to check for errors**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/frontend && npx vite build
```
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/views/MyApplicationsPage.vue && \
  git commit -m "feat: MyApplicationsPage summary cards + drawer integration

Replaces inline stepper and action buttons with a compact summary card
that opens ApplicationDetailDrawer. Uses the new applications store."
```

---

### Task 7: Frontend — ProjectDetailPage refactor

**Files:**
- Modify: `frontend/src/views/ProjectDetailPage.vue`

Applications list (owner view) becomes clickable rows that open the drawer. Student's own-application section keeps the at-a-glance summary but replaces action buttons with a "View full history & actions" button that opens the drawer. Review form and chat buttons stay where they are.

- [ ] **Step 1: Add imports and store in `<script setup>`**

In `frontend/src/views/ProjectDetailPage.vue`, replace the import block (lines 196–208) with:

```js
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useProjectsStore } from '@/stores/projects'
import { useApplicationsStore } from '@/stores/applications'
import { filesAPI, reviewsAPI, chatAPI } from '@/api'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import FileUpload from '@/components/FileUpload.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import ApplicationDetailDrawer from '@/components/ApplicationDetailDrawer.vue'
```

- [ ] **Step 2: Add the applications store and drawer state, remove local `applications` ref**

In `frontend/src/views/ProjectDetailPage.vue`, replace the lines:

```js
const projectsStore = useProjectsStore()

const project = ref(null)
const applications = ref([])
const myApp = ref(null)
```

with:

```js
const projectsStore = useProjectsStore()
const applicationsStore = useApplicationsStore()

const project = ref(null)
const applications = computed(() => applicationsStore.byProject[route.params.id] || [])
const myApp = ref(null)
const drawerApp = ref(null)
const drawerView = ref('student')
```

- [ ] **Step 3: Update the `load` function to use the store and drop inline app fetches**

Replace the `load` function (lines 236–253) with:

```js
async function load() {
  const id = route.params.id
  try {
    await projectsStore.fetchOne(id)
    project.value = projectsStore.currentProject
    try { attachments.value = (await filesAPI.list(id, 'attachment')).data } catch {}
    try { submissions.value = (await filesAPI.list(id, 'submission')).data } catch {}
    if (isOwner.value || auth.isAdmin) {
      await applicationsStore.fetchByProject(id)
    }
    if (auth.isStudent) {
      await applicationsStore.fetchMy()
      myApp.value = applicationsStore.myApps.find(a => a.project_id === Number(id)) || null
    }
  } catch { router.push('/projects') }
}
```

- [ ] **Step 4: Replace the `updateApp` and `updateMyApp` handlers with store calls + add drawer openers**

Replace `updateApp` / `updateMyApp` (lines 265–277) with:

```js
async function onApplicationAction() {
  // Drawer already patched the store; sync local myApp for the student view
  if (auth.isStudent) {
    myApp.value = applicationsStore.myApps.find(a => a.project_id === Number(route.params.id)) || null
  }
  toast.success('Status updated')
}

function openOwnerDrawer(app) {
  drawerView.value = 'company'
  drawerApp.value = app
}

function openMyAppDrawer() {
  if (!myApp.value) return
  drawerView.value = 'student'
  drawerApp.value = myApp.value
}

function closeDrawer() {
  drawerApp.value = null
}
```

- [ ] **Step 5: Replace the "My Application" template section with drawer-opener**

In the template, replace the `<section v-if="myApp" class="detail-section">` block (lines 87–114) with:

```html
    <!-- My Application Status -->
    <section v-if="myApp" class="detail-section">
      <h2>Your Application</h2>
      <div class="app-status-card">
        <div class="app-status-row">
          <StatusBadge :status="myApp.status" />
          <span class="text-muted">{{ fmtDate(myApp.updated_at) }}</span>
        </div>
        <p v-if="myApp.cover_letter" class="text-secondary">{{ myApp.cover_letter }}</p>
        <p v-if="myApp.revision_note" class="revision-note">
          <span class="material-icons-round">edit_note</span>Revision: {{ myApp.revision_note }}
        </p>
        <div class="app-actions">
          <button class="btn btn-primary btn-sm" @click="openMyAppDrawer">
            <span class="material-icons-round">timeline</span>View full history &amp; actions
          </button>
          <button v-if="myApp.status !== 'rejected'" class="btn btn-secondary btn-sm" @click="openChat">
            <span class="material-icons-round">chat_bubble_outline</span>Message Owner
          </button>
        </div>
      </div>
    </section>
```

- [ ] **Step 6: Replace the owner "Applications" template section with clickable rows**

In the template, replace the `<section v-if="isOwner" class="detail-section">` block (lines 116–163) with:

```html
    <!-- Applications List (owner) -->
    <section v-if="isOwner" class="detail-section">
      <h2>Applications ({{ applications.length }})</h2>
      <div v-if="applications.length" class="apps-list">
        <div v-for="a in applications" :key="a.id" class="app-card">
          <div class="app-card-row" @click="openOwnerDrawer(a)">
            <router-link :to="`/profile/${a.applicant_id}`" class="app-user-link" @click.stop>
              <div class="av-sm">{{ String(a.applicant_id).charAt(0) }}</div>
              User #{{ a.applicant_id }}
            </router-link>
            <div class="app-card-meta">
              <span class="text-muted">{{ latestSummary(a) }}</span>
              <StatusBadge :status="a.status" />
              <span class="material-icons-round chev">chevron_right</span>
            </div>
          </div>
          <div v-if="a.status === 'completed' || a.status === 'approved'" class="app-review-row">
            <div v-if="!reviewedApps.has(a.id)" class="review-form">
              <h4>Leave Review</h4>
              <div class="star-select">
                <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: (reviewData[a.id]?.rating || 0) >= n }" @click="setRating(a.id, n)">&#9733;</button>
              </div>
              <input class="input" v-model="reviewComments[a.id]" placeholder="Comment..." />
              <button class="btn btn-primary btn-sm" @click="submitReview(a.id, a.applicant_id)">Submit Review</button>
            </div>
            <span v-else class="text-muted">Reviewed</span>
          </div>
          <button v-if="a.status !== 'rejected'" class="btn btn-ghost btn-sm chat-btn" @click="openChatWith(a.applicant_id)">
            <span class="material-icons-round">chat_bubble_outline</span>Chat
          </button>
        </div>
      </div>
      <EmptyState v-else icon="inbox" title="No applications yet" subtitle="Applications will appear here when students apply" />
    </section>
```

- [ ] **Step 7: Add `latestSummary` helper and drawer element**

In `<script setup>`, after `fmtDate` / `formatSize`, add:

```js
const STATUS_LABELS_PD = {
  pending: 'Pending', accepted: 'Accepted', rejected: 'Rejected',
  in_progress: 'In Progress', submitted: 'Submitted',
  revision_requested: 'Revision Requested', approved: 'Approved', completed: 'Completed',
}

function latestSummary(app) {
  const hist = app.status_history || []
  if (!hist.length) return `Applied ${fmtDate(app.created_at)}`
  const latest = hist[hist.length - 1]
  return `${STATUS_LABELS_PD[latest.status] || latest.status} · ${fmtDate(latest.timestamp)}`
}
```

In the template, just before the closing `</div>` of the outer `<div v-if="project" class="page container">` (right after the `<ConfirmDialog ... />` tag), add:

```html
    <ApplicationDetailDrawer
      :application="drawerApp"
      :view-as="drawerView"
      @close="closeDrawer"
      @action-complete="onApplicationAction"
    />
```

- [ ] **Step 8: Add supporting CSS**

In the `<style scoped>` block of `frontend/src/views/ProjectDetailPage.vue`, add these rules before the closing `</style>`:

```css
.app-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 2px;
  border-radius: var(--radius-md);
}
.app-card-row:hover { background: var(--gray-50); }
.app-card-meta { display: flex; align-items: center; gap: 10px; }
.app-card-meta .chev { color: var(--gray-400); font-size: 18px; }
.app-review-row { margin-top: 10px; }
.chat-btn { margin-top: 8px; }
```

- [ ] **Step 9: Run the frontend build**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/frontend && npx vite build
```
Expected: Build succeeds.

- [ ] **Step 10: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/views/ProjectDetailPage.vue && \
  git commit -m "feat: ProjectDetailPage uses applications store + drawer

Owner applications list becomes clickable rows opening the drawer;
student's own-application section gets a 'View full history & actions'
button. Inline workflow buttons removed — all actions live in the
drawer now."
```

---

### Task 8: Frontend — Dashboard sections use the applications store

**Files:**
- Modify: `frontend/src/components/dashboard/DashboardStudentSection.vue`
- Modify: `frontend/src/components/dashboard/DashboardCompanySection.vue`

- [ ] **Step 1: Update `DashboardStudentSection.vue`**

Replace the import block and the `onMounted` body.

Replace the imports (lines 91–97):

```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { applicationsAPI, projectsAPI, reviewsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
```

with:

```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI, reviewsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
```

Replace (lines 99–109):

```js
const auth = useAuthStore()
const apps = ref([])
const projectTitles = ref({})
const rating = ref(null)
const suggestedProjects = ref([])
const loading = ref(true)

const allApps = ref([])
const activeStatuses = ['pending', 'accepted', 'in_progress', 'submitted', 'revision_requested', 'approved']
const activeCount = computed(() => allApps.value.filter(a => activeStatuses.includes(a.status)).length)
const completedCount = computed(() => allApps.value.filter(a => a.status === 'completed').length)
```

with:

```js
const auth = useAuthStore()
const applicationsStore = useApplicationsStore()
const projectTitles = ref({})
const rating = ref(null)
const suggestedProjects = ref([])
const loading = ref(true)

const activeStatuses = ['pending', 'accepted', 'in_progress', 'submitted', 'revision_requested', 'approved']
const apps = computed(() => applicationsStore.myApps.slice(0, 5))
const activeCount = computed(() => applicationsStore.myApps.filter(a => activeStatuses.includes(a.status)).length)
const completedCount = computed(() => applicationsStore.myApps.filter(a => a.status === 'completed').length)
```

Replace the `onMounted` body (lines 119–153):

```js
onMounted(async () => {
  try {
    const [ratingRes, projectsRes] = await Promise.allSettled([
      reviewsAPI.rating(auth.user.id),
      projectsAPI.list({ page: 1, size: 4, status: 'open' }),
    ])

    await applicationsStore.fetchMy()

    // Resolve project titles for the first 5 applications in parallel
    const uniqueIds = [...new Set(apps.value.map(a => a.project_id))]
    const titleResults = await Promise.allSettled(
      uniqueIds.map(id => projectsAPI.get(id))
    )
    titleResults.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        projectTitles.value[uniqueIds[i]] = r.value.data.title
      }
    })

    if (ratingRes.status === 'fulfilled') {
      rating.value = ratingRes.value.data
    }
    if (projectsRes.status === 'fulfilled') {
      suggestedProjects.value = projectsRes.value.data.items
    }
  } catch (err) {
    console.error('DashboardStudentSection load error:', err)
  } finally {
    loading.value = false
  }
})
```

- [ ] **Step 2: Update `DashboardCompanySection.vue`**

Replace the imports (lines 94–100):

```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, applicationsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
```

with:

```js
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
```

Add the store reference to the `<script setup>` variables. Replace (line 102):

```js
const auth = useAuthStore()
```

with:

```js
const auth = useAuthStore()
const applicationsStore = useApplicationsStore()
```

Replace the `onMounted` body (lines 125–155):

```js
onMounted(async () => {
  try {
    const { data } = await projectsAPI.list({ owner_id: auth.user.id, page: 1, size: 5 })
    myProjects.value = data.items
    myProjectsTotal.value = data.total
    myProjects.value.forEach(p => { projectTitles.value[p.id] = p.title })

    // Fetch applications for each project in parallel via the store
    await Promise.allSettled(
      myProjects.value.map(p => applicationsStore.fetchByProject(p.id))
    )

    let allPending = []
    myProjects.value.forEach(p => {
      const projectApps = applicationsStore.byProject[p.id] || []
      appCounts.value[p.id] = projectApps.length
      allPending.push(...projectApps.filter(a => a.status === 'pending'))
    })

    allPending.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    totalPending.value = allPending.length
    pendingApps.value = allPending.slice(0, 5)
  } catch (err) {
    console.error('DashboardCompanySection load error:', err)
  } finally {
    loading.value = false
  }
})
```

- [ ] **Step 3: Run the frontend build**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/frontend && npx vite build
```
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /Users/temporary/Developer/WorkWithUs && \
  git add frontend/src/components/dashboard/DashboardStudentSection.vue \
          frontend/src/components/dashboard/DashboardCompanySection.vue && \
  git commit -m "refactor: dashboard sections consume applications store

Both student and company sections now read from the Pinia applications
store instead of calling applicationsAPI directly, giving them live
updates when status changes from elsewhere in the app."
```

---

### Task 9: Final verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/backend && python3 -m pytest src/tests/ -v
```
Expected: All tests pass (65 existing + 3 new = 68 total).

- [ ] **Step 2: Run the frontend build**

Run:
```bash
cd /Users/temporary/Developer/WorkWithUs/frontend && npx vite build
```
Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit (only if fixes were required)**

If either verification step failed and required fixes that weren't already committed, commit them with a descriptive message. Otherwise skip.
