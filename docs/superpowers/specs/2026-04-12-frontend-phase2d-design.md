# Frontend Phase 2D: Project Discovery

## Overview

Improve the project discovery experience by extending backend search/filtering and adding sort options and skill-based matching to the frontend. Students can match projects to their profile skills with one click.

**Scope:** 1 modified backend router, 1 modified frontend view. No new endpoints, stores, or components.

## 1. Backend: Extended List Projects Endpoint

### File
- Modify: `backend/src/projects/router.py`

### Changes to `_build_project_filter`

**Extended search** — Currently `title__icontains` only. Change to OR across three fields:
```python
if search:
    q = q.filter(
        Q(title__icontains=search) |
        Q(description__icontains=search) |
        Q(required_skills__name__icontains=search)
    )
```
The skill join can produce duplicates, so the query in `list_projects` must add `.distinct()`.

**Skill matching** — New parameter `skill_ids: Optional[list[int]]`. When provided, filter to projects that have at least one of the given skills:
```python
if skill_ids:
    q = q.filter(required_skills__id__in=skill_ids)
```
This is OR logic — projects matching any of the provided skill IDs are included.

### Changes to `list_projects`

**New query params:**
- `skill_ids: Optional[list[int]] = Query(None)` — list of skill IDs for filtering
- `sort: Optional[str] = Query("newest")` — sort order: `newest` or `deadline`

**Sort logic** — Replace hardcoded `.order_by("-created_at")` with:
- `newest` → `.order_by("-created_at")` (default, same as current)
- `deadline` → `.order_by("deadline")` — Tortoise ORM puts nulls last by default on ascending sort, which is the desired behavior (projects without deadlines appear at the end)

**Distinct** — Add `.distinct()` to the query chain to handle duplicates from skill joins.

**Pass `skill_ids` to `_build_project_filter`** — Add the parameter to both the function signature and the call site.

### Testing
- Existing tests continue to pass (default behavior unchanged)
- New test: search matches description text
- New test: search matches skill name
- New test: `skill_ids` filter returns only projects with matching skills
- New test: `sort=deadline` orders by deadline ascending
- New test: combining `skill_ids` + `search` + `status` works together

## 2. Frontend: ProjectsPage Enhancements

### File
- Modify: `frontend/src/views/ProjectsPage.vue`

### New state
```js
const sortBy = ref('newest')       // 'newest' | 'deadline'
const matchSkills = ref(false)     // toggle for skill matching
```

### Filter bar changes

Current layout: `[search] [status] [type]`
New layout: `[search] [status] [type] [sort] [Match My Skills button]`

**Sort select** — New `<select>` with two options:
- "Newest" (`newest`) — default
- "Deadline" (`deadline`)
- Triggers `fetchProjects()` on change

**Match My Skills button** — Visible only when `auth.isStudent && auth.user?.skills?.length > 0`:
- Renders as a `<button>` with text "Match My Skills" and a sparkle/auto_awesome icon
- When active: highlighted with accent background (`.match-active` class)
- Click toggles `matchSkills`, resets `page` to 1, calls `fetchProjects()`
- When inactive, no `skill_ids` param is sent

### fetchProjects changes

```js
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
```

### Styling

**Match button styles:**
```css
.match-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: var(--white);
  font-size: .8125rem;
  cursor: pointer;
  transition: all .15s ease;
}
.match-btn:hover { border-color: var(--gray-300); }
.match-active {
  background: var(--accent);
  color: var(--white);
  border-color: var(--accent);
}
.match-active:hover { opacity: 0.9; }
```

The sort select uses the existing `.input.select` classes — no new styles needed.

## 3. API Layer

### File
- Modify: `frontend/src/api/index.js`

### Axios paramsSerializer

Axios 1.x serializes arrays as `skill_ids[]=1&skill_ids[]=2` by default, but FastAPI expects repeated keys: `skill_ids=1&skill_ids=2`. Add a `paramsSerializer` to the Axios instance:

```js
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  paramsSerializer: { indexes: null },
})
```

The `{ indexes: null }` option tells Axios to serialize arrays without brackets — producing `skill_ids=1&skill_ids=2`, which FastAPI accepts natively.

## Files Summary

| Action | File | Changes |
|--------|------|---------|
| Modify | `backend/src/projects/router.py` | Extended search, skill_ids filter, sort param, distinct |
| Modify | `frontend/src/api/index.js` | Add paramsSerializer for array param compatibility |
| Modify | `frontend/src/views/ProjectsPage.vue` | Sort dropdown, Match My Skills toggle, updated fetch |
