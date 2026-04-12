# Frontend Phase 2D: Project Discovery — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve project discovery by extending backend search/filtering (description + skills), adding sort options, and adding a "Match My Skills" button for students.

**Architecture:** Backend `list_projects` endpoint gets three new query params (`skill_ids`, `sort`, extended `search`). Frontend `ProjectsPage` adds a sort dropdown and a skill-matching toggle button. Axios config updated for array param serialization.

**Tech Stack:** FastAPI, Tortoise ORM Q objects, Vue 3 Composition API, Axios

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `backend/src/projects/router.py` | Extended search, skill_ids filter, sort param |
| Create | `backend/src/tests/test_discovery.py` | Tests for new discovery features |
| Modify | `frontend/src/api/index.js` | Axios paramsSerializer for array params |
| Modify | `frontend/src/views/ProjectsPage.vue` | Sort dropdown, Match My Skills toggle |

---

### Task 1: Backend — Extended search, skill filter, and sort

**Files:**
- Modify: `backend/src/projects/router.py`
- Create: `backend/src/tests/test_discovery.py`

- [ ] **Step 1: Write the tests**

Create `backend/src/tests/test_discovery.py`:

```python
import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


@pytest.mark.asyncio
async def test_search_matches_description(client: AsyncClient, company_token: str):
    """Search should match project description, not just title."""
    await client.post("/api/v1/projects/", json={
        "title": "Generic Title", "description": "Build a machine learning pipeline"
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=machine+learning")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert any("machine learning" in p["description"].lower() for p in r.json()["items"])


@pytest.mark.asyncio
async def test_search_matches_skill_name(client: AsyncClient, company_token: str, student_token: str):
    """Search should match required skill names."""
    # Create a skill
    skill_resp = await client.post("/api/v1/skills/", json={
        "name": "TensorFlow", "category": "ML"
    }, headers=auth(student_token))
    skill_id = skill_resp.json()["id"]

    # Create project with that skill
    await client.post("/api/v1/projects/", json={
        "title": "Data Project", "description": "A data project",
        "skill_ids": [skill_id],
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=TensorFlow")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_skill_ids(client: AsyncClient, company_token: str, student_token: str):
    """skill_ids param should filter to projects with matching skills."""
    s1 = await client.post("/api/v1/skills/", json={"name": "React"}, headers=auth(student_token))
    s2 = await client.post("/api/v1/skills/", json={"name": "Django"}, headers=auth(student_token))
    sid1, sid2 = s1.json()["id"], s2.json()["id"]

    # Project with React
    await client.post("/api/v1/projects/", json={
        "title": "React App", "description": "Frontend application",
        "skill_ids": [sid1],
    }, headers=auth(company_token))

    # Project with Django
    await client.post("/api/v1/projects/", json={
        "title": "Django API", "description": "Backend application",
        "skill_ids": [sid2],
    }, headers=auth(company_token))

    # Filter by React only
    r = await client.get(f"/api/v1/projects/?skill_ids={sid1}")
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()["items"]]
    assert "React App" in titles
    assert "Django API" not in titles

    # Filter by both (OR logic)
    r = await client.get(f"/api/v1/projects/?skill_ids={sid1}&skill_ids={sid2}")
    assert r.status_code == 200
    assert r.json()["total"] >= 2


@pytest.mark.asyncio
async def test_sort_by_deadline(client: AsyncClient, company_token: str):
    """sort=deadline should order by deadline ascending, nulls last."""
    await client.post("/api/v1/projects/", json={
        "title": "No Deadline", "description": "Project without deadline",
    }, headers=auth(company_token))

    await client.post("/api/v1/projects/", json={
        "title": "Soon Deadline", "description": "Project with near deadline",
        "deadline": "2026-05-01T00:00:00",
    }, headers=auth(company_token))

    await client.post("/api/v1/projects/", json={
        "title": "Late Deadline", "description": "Project with later deadline",
        "deadline": "2026-12-01T00:00:00",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?sort=deadline")
    assert r.status_code == 200
    items = r.json()["items"]
    # Projects with deadlines should come before null-deadline projects
    deadlined = [p for p in items if p["deadline"] is not None]
    assert len(deadlined) >= 2
    # Earlier deadline should come first
    assert deadlined[0]["title"] == "Soon Deadline"
    assert deadlined[1]["title"] == "Late Deadline"


@pytest.mark.asyncio
async def test_sort_newest_is_default(client: AsyncClient, company_token: str):
    """Default sort (newest) should return most recent first."""
    await client.post("/api/v1/projects/", json={
        "title": "First Created", "description": "Created first in time",
    }, headers=auth(company_token))
    await client.post("/api/v1/projects/", json={
        "title": "Second Created", "description": "Created second in time",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["title"] == "Second Created"


@pytest.mark.asyncio
async def test_combined_filters(client: AsyncClient, company_token: str, student_token: str):
    """skill_ids + search + status should all work together."""
    skill = await client.post("/api/v1/skills/", json={"name": "Kotlin"}, headers=auth(student_token))
    sid = skill.json()["id"]

    await client.post("/api/v1/projects/", json={
        "title": "Android App", "description": "Mobile development project",
        "skill_ids": [sid],
    }, headers=auth(company_token))

    r = await client.get(f"/api/v1/projects/?skill_ids={sid}&search=mobile&status=open")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_existing_search_still_works(client: AsyncClient, company_token: str):
    """Title search (existing behavior) must not break."""
    await client.post("/api/v1/projects/", json={
        "title": "Unique Title XYZ", "description": "Some description",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=Unique+Title")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest src/tests/test_discovery.py -v
```

Expected: `test_search_matches_description` and `test_search_matches_skill_name` FAIL (search only checks title). `test_filter_by_skill_ids` FAIL (no skill_ids param). `test_sort_by_deadline` FAIL (no sort param). Others may pass/fail depending on current behavior.

- [ ] **Step 3: Implement the backend changes**

Modify `backend/src/projects/router.py`:

**Add Q import** — at the top, add:

```python
from tortoise.queryset import Q
```

**Replace `_build_project_filter`** (lines 70-81) with:

```python
def _build_project_filter(status=None, owner_id=None, is_student_project=None, search=None, skill_ids=None):
    filters = {}
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id
    if is_student_project is not None:
        filters["is_student_project"] = is_student_project
    q = Project.filter(**filters)
    if skill_ids:
        q = q.filter(required_skills__id__in=skill_ids)
    if search:
        q = q.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(required_skills__name__icontains=search)
        )
    return q
```

**Replace `list_projects`** (lines 113-123) with:

```python
@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None, owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None, search: Optional[str] = None,
    skill_ids: Optional[list[int]] = Query(None),
    sort: Optional[str] = Query("newest"),
):
    skip = (page - 1) * size
    q = _build_project_filter(status, owner_id, is_student_project, search, skill_ids)
    total = await q.distinct().count()
    order = "deadline" if sort == "deadline" else "-created_at"
    items = await q.prefetch_related("required_skills", "attachments").distinct().order_by(order).offset(skip).limit(size)
    return {"items": items, "total": total, "page": page, "size": size}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest src/tests/test_discovery.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
cd backend && python -m pytest src/tests/ -v
```

Expected: All tests pass (existing + new).

- [ ] **Step 6: Commit**

```bash
git add backend/src/projects/router.py backend/src/tests/test_discovery.py
git commit -m "feat: extend project list with description/skill search, skill_ids filter, sort param"
```

---

### Task 2: Frontend — Axios paramsSerializer

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: Add paramsSerializer to Axios instance**

In `frontend/src/api/index.js`, change the `axios.create` call (line 3-6) from:

```js
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})
```

to:

```js
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  paramsSerializer: { indexes: null },
})
```

This makes Axios serialize arrays as `skill_ids=1&skill_ids=2` instead of `skill_ids[]=1&skill_ids[]=2`, which FastAPI expects.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "fix: configure Axios paramsSerializer for FastAPI array param compatibility"
```

---

### Task 3: Frontend — ProjectsPage sort and skill matching

**Files:**
- Modify: `frontend/src/views/ProjectsPage.vue`

- [ ] **Step 1: Update the template**

Replace the entire `<template>` section of `frontend/src/views/ProjectsPage.vue` with:

```html
<template>
  <div class="page container">
    <header class="page-header">
      <div>
        <h1>Projects</h1>
        <p class="page-sub">{{ store.total }} projects available</p>
      </div>
      <router-link v-if="auth.isAuth" to="/projects/create" class="btn btn-primary">
        <span class="material-icons-round">add</span>New Project
      </router-link>
    </header>

    <div class="filters-bar">
      <div class="search-box">
        <span class="material-icons-round">search</span>
        <input class="input" v-model="search" placeholder="Search projects..." @input="debouncedFetch" />
      </div>
      <div class="filter-group">
        <select class="input select" v-model="statusFilter" @change="fetchProjects">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
        <select class="input select" v-model="typeFilter" @change="fetchProjects">
          <option value="">All Types</option>
          <option value="false">Company</option>
          <option value="true">Student</option>
        </select>
        <select class="input select" v-model="sortBy" @change="fetchProjects">
          <option value="newest">Newest</option>
          <option value="deadline">Deadline</option>
        </select>
        <button
          v-if="auth.isStudent && auth.user?.skills?.length"
          class="match-btn"
          :class="{ 'match-active': matchSkills }"
          @click="toggleMatchSkills"
        >
          <span class="material-icons-round">auto_awesome</span>
          Match My Skills
        </button>
      </div>
    </div>

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
      <span class="material-icons-round">folder_open</span>
      <h3>No projects found</h3>
      <p>Try adjusting your filters or search query</p>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; fetchProjects()">
        <span class="material-icons-round">chevron_left</span>
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++; fetchProjects()">
        <span class="material-icons-round">chevron_right</span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Update the script**

Replace the entire `<script setup>` section with:

```js
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const sortBy = ref('newest')
const matchSkills = ref(false)
const totalPages = computed(() => Math.ceil(store.total / size))

let timer
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchProjects() }, 300) }
onUnmounted(() => clearTimeout(timer))

function toggleMatchSkills() {
  matchSkills.value = !matchSkills.value
  page.value = 1
  fetchProjects()
}

async function fetchProjects() {
  const params = { page: page.value, size }
  if (search.value) params.search = search.value
  if (statusFilter.value) params.status = statusFilter.value
  if (typeFilter.value !== '') params.is_student_project = typeFilter.value === 'true'
  if (sortBy.value !== 'newest') params.sort = sortBy.value
  if (matchSkills.value && auth.user?.skills?.length) {
    params.skill_ids = auth.user.skills.map(s => s.id)
  }
  await store.fetchList(params)
}

onMounted(fetchProjects)
</script>
```

- [ ] **Step 3: Update the styles**

Replace the entire `<style scoped>` section with:

```css
<style scoped>
.page { padding: 2rem 24px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
.page-sub { color: var(--gray-400); font-size: .8125rem; margin-top: 2px; }
.filters-bar { display: flex; gap: 10px; margin-bottom: 1.5rem; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 220px; position: relative; display: flex; align-items: center; }
.search-box .material-icons-round { position: absolute; left: 12px; color: var(--gray-400); font-size: 18px; }
.search-box .input { padding-left: 36px; width: 100%; }
.filter-group { display: flex; gap: 8px; flex-wrap: wrap; }
.select { min-width: 140px; }
.projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 1.5rem; }
.page-info { font-size: .8125rem; color: var(--gray-500); }
.match-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: var(--white);
  font-size: .8125rem;
  cursor: pointer;
  transition: all .15s ease;
  white-space: nowrap;
}
.match-btn:hover { border-color: var(--gray-300); }
.match-btn .material-icons-round { font-size: 16px; }
.match-active {
  background: var(--accent);
  color: var(--white);
  border-color: var(--accent);
}
.match-active:hover { opacity: 0.9; }
</style>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ProjectsPage.vue
git commit -m "feat: add sort dropdown and Match My Skills button to ProjectsPage"
```

---

### Task 4: Build verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run backend tests**

```bash
cd backend && python -m pytest src/tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npx vite build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit (only if fixes were needed)**

Only commit if you had to fix anything.
