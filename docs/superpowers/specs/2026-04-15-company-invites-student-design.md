# Company Invites Student (Inverse Flow) — Design

**Status:** Design
**Date:** 2026-04-15
**Scope:** Backend + frontend feature enabling companies to search students and directly invite them to projects, inverting the existing student-applies-to-project workflow.

## 1. Problem

Today the platform only supports a single initiation direction: a student browses open projects and submits an application (`POST /applications/`). Companies cannot proactively recruit. They have no way to discover students by skills, rating, or availability, and no way to open the workflow from their side.

## 2. Goals

- Companies can search students by skills (AND semantics), minimum rating, availability, and free-text name match.
- Companies can send an invitation to a specific student for a specific open project.
- Students receive an in-app notification for each invite and can accept or decline from the same UI they already use to track applications.
- Accepting an invite drops the record into the existing workflow at `accepted`, with zero special-case code for downstream states.
- Companies can withdraw an unanswered invite.

## 3. Non-goals

- No bulk invites ("invite these 10 students"). Each invite is one student, one project.
- No invitation expiry / auto-cancel. Invites stay `invited` until someone acts.
- No re-invite cooldown after a decline. If the company invites the same student to a **different** project, that is allowed. Same project is blocked by the existing unique constraint.
- No negotiation step (student cannot counter-propose).
- No self-reported availability toggle on `StudentProfile`. Availability is derived from active applications.

## 4. Architecture

One-table approach: invites live in the existing `applications` table. Two additions: an `invited` status, and an `initiator` column (`student` | `company`). All downstream workflow (`accepted → in_progress → submitted → …`) is reused unchanged.

Rationale: the fields overlap almost completely (project, applicant, cover letter / message, status, status_history). A separate `Invitation` entity would duplicate schema and double every cross-cutting concern (notifications, permissions, status history). The only cost of the shared-table approach is one extra enum value and one extra column, both trivially additive.

## 5. Data model

### 5.1 New enum

```python
# src/applications/models.py
class ApplicationInitiator(str, enum.Enum):
    student = "student"
    company = "company"
```

### 5.2 Extend `ApplicationStatus`

Add `invited = "invited"` at the top of the enum. All existing values unchanged.

### 5.3 Extend `Application`

Add one column:

```python
initiator = fields.CharEnumField(
    enum_type=ApplicationInitiator,
    default=ApplicationInitiator.student,
)
```

Default `student` backfills every existing row correctly — all current rows came from the student-applies path.

Unique constraint `(project, applicant)` is retained. This naturally enforces:

- A student cannot receive two simultaneous invites for the same project.
- A student cannot apply to a project they have already been invited to (they respond to the invite instead).
- A company cannot re-invite to the same project after withdrawal or decline (would require DELETE + recreate; we do not delete rows).

### 5.4 Migration

One Aerich migration: `aerich migrate --name "add_invited_status_and_initiator"` on current head. No data migration required because the new column has a default and the new enum value is additive.

## 6. Workflow

### 6.1 State machine

New transitions added to `VALID_TRANSITIONS` in `src/applications/service.py`:

```
invited → accepted   (student accepts)
invited → rejected   (student declines OR company withdraws)
```

All other transitions stay exactly as they are. `accepted → in_progress → submitted → …` is identical for both initiation paths.

### 6.2 Actor rules

| From → To              | Allowed actor                          | Note |
|------------------------|----------------------------------------|------|
| `invited → accepted`   | `current_user.id == applicant_id`      | Student accepting invite. |
| `invited → rejected`   | `current_user.id == applicant_id` OR `current_user.id == project.owner_id` | Student declines or company withdraws. |
| `pending → accepted/rejected` | project owner or admin (unchanged) | Existing rule. |

The actor is recorded in `status_history[-1].actor_id` / `actor_name`, so the frontend can distinguish a company-withdrawn invite from a student-declined invite.

### 6.3 Side-effects on accept

When `invited → accepted` fires, the existing `update_status` logic already:

- Adds the student to the project team (`teams_repo.add_member`), promoting to lead if no lead exists yet.

No extra branch needed. Completion counter, team lead promotion, and later transitions all just work.

## 7. Endpoints

### 7.1 `GET /api/v1/users/search`

New route in `src/users/router.py`. Guard: `current_user.role in {company, admin}` (403 otherwise).

Query params:

| Name         | Type            | Notes |
|--------------|-----------------|-------|
| `skills`     | repeated int    | Skill IDs. AND semantics — student must have all. |
| `min_rating` | float 0–5       | Filter `StudentProfile.rating >= min_rating`. |
| `available`  | bool (default false) | When true, exclude students with any application whose status ∈ {accepted, in_progress, submitted, revision_requested, approved}. |
| `q`          | string          | ILIKE match against `username` and `full_name`. |
| `page`       | int, default 1  | |
| `size`       | int, default 20, max 50 | |

Implementation: single Tortoise query joining `users`, `user_skills`, `student_profiles`, with `HAVING COUNT(DISTINCT skill_id) = len(skills)` for the AND filter. Availability computed via a `NOT EXISTS` subquery on `applications`. Only `role=student AND is_active=true AND is_blocked=false` users returned.

Response:

```json
{
  "total": 42,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 7,
      "username": "alice",
      "full_name": "Alice Chen",
      "avatar_url": "https://...",
      "bio": "...",
      "skills": [{ "id": 3, "name": "Python", "category": "language" }],
      "rating": 4.6,
      "completed_projects_count": 5,
      "is_available": true
    }
  ]
}
```

Cached in Redis for 60s keyed by the normalized query string — companies scroll/refilter rapidly and the underlying data changes slowly.

### 7.2 `POST /api/v1/applications/invite`

Body: `{ project_id: int, student_id: int, message: str | None }`.

Guard order (first failure wins):

1. `current_user.role == company` — else 403.
2. Project exists and `owner_id == current_user.id` — else 404 / 403.
3. Project `status == "open"` — else 400 "Project is not open".
4. Target user exists and `role == student` — else 400 "Target user is not a student".
5. No existing row for `(project_id, student_id)` — else 400 "Student already invited or applied".
6. `count_active(project_id) < max_participants` — else 400 "Project is at capacity".

On success, creates:

```python
Application(
    project_id, applicant_id=student_id,
    cover_letter=message,
    status=ApplicationStatus.invited,
    initiator=ApplicationInitiator.company,
    status_history=[{
        "status": "invited", "timestamp": now,
        "actor_id": current_user.id,
        "actor_name": current_user.full_name or current_user.username,
        "note": None,
    }],
)
```

Side-effects (in order):

1. `create_notification(student_id, title="Invitation: <project.title>", message=<message or truncated project excerpt>, notification_type="invite", link="/applications")`.
2. `bg.add_task(send_application_invite_email, student.email, student.username, project.title, company.username)` — see §10 for email fallback behavior.
3. `log_activity(current_user.id, "invite", ...)`.

Returns the created `Application` via `ApplicationResponse`.

### 7.3 `PUT /api/v1/applications/:id/status` — extended

No new route — existing endpoint handles the new transitions. Implementation changes in `src/applications/service.update_status`:

- Add `invited` to `VALID_TRANSITIONS`.
- When current status is `invited`:
  - `new_status == accepted`: require `current_user.id == application.applicant_id`.
  - `new_status == rejected`: allow if `current_user.id == application.applicant_id` OR `current_user.id == project.owner_id`.
- Notification fan-out additions (mirroring the existing `owner_statuses` pattern):
  - Student accepts → notify project owner ("Accepted your invite").
  - Student declines → notify project owner ("Declined your invite", with optional reason).
  - Company withdraws → notify student ("Invitation withdrawn").

### 7.4 `ApplicationResponse` schema

Add one field: `initiator: ApplicationInitiator`. Frontend uses it to distinguish "invites I received" from "invites I sent" visually.

## 8. Frontend

### 8.1 New page — `/students`

File: `frontend/src/views/StudentsPage.vue`. Route metadata: `{ requiresAuth: true, roles: ['company', 'admin'] }`. Navbar renders the "Students" link only when `auth.user?.role === 'company'`.

Layout mirrors `ProjectsPage`:

- Left: filter panel — reused `SkillPicker` for multi-select skill filter, number input for `min_rating`, checkbox "Available only", debounced free-text `q` input.
- Right: paginated grid of student cards. Card shows avatar, name, skill chips, `⭐ rating · N completed`, and a primary "Invite" button. Clicking the card body navigates to `/profile/:id`; the button stops propagation and opens `InviteStudentModal`. Loading uses `SkeletonBlock`, empty uses `EmptyState`.

### 8.2 Invite modal — `InviteStudentModal.vue`

Built on `BaseModal`. Opened from:

- "Invite" button on each student search card.
- "Invite to Project" button on `ProfilePage` when `auth.user?.role === 'company' && profile user is student && !isMe`.

Fields:

- Project `<select>` — populated from `projectsAPI.list({ owner_id: auth.user.id, status: 'open' })`. Projects at capacity show "(full)" and are disabled. Empty state shows a CTA "You have no open projects — [Create one]" linking to `/projects/new`.
- Message `<textarea>` (optional, uses `FormField`).
- Submit calls `applicationsAPI.invite({ project_id, student_id, message })`.

On success: toast "Invitation sent", close modal, do not navigate. Backend errors (especially the "already invited or applied" 400) surface inline under the project `<select>`.

### 8.3 API client — `frontend/src/api/index.js`

Two additions:

```js
usersAPI.search = (params) => api.get('/users/search', { params })
applicationsAPI.invite = (d) => api.post('/applications/invite', d)
```

### 8.4 Pinia store — `stores/applications.js`

Add `invite(payload)` which calls `applicationsAPI.invite`. The returned row does **not** belong in `myApps` (that is the current user's incoming/outgoing applications list; a company inviting a student doesn't add anything to the company's own `myApps`). The store simply resolves with the data; no in-place mutation. (Note: `myApps` remains keyed by "applications where `applicant_id == current_user.id`", which means on the student side it already includes invites received — no change to the store's `fetchMy` contract.)

### 8.5 `MyApplicationsPage.vue`

Two small changes:

1. `latestSummary(app)` additionally checks `initiator` + `status`. When `status === 'invited' && initiator === 'company'`, the card footer shows "You were invited — awaiting your response" instead of "Applied <date>".
2. The card opens the existing `ApplicationDetailDrawer` — no structural change; drawer handles the new buttons.

### 8.6 `ApplicationDetailDrawer.vue`

Extend the `actionButtons` computed:

```js
if (props.viewAs === 'student') {
  if (s === 'invited') return [
    { status: 'accepted', label: 'Accept Invitation', icon: 'check', class: 'btn btn-primary btn-sm' },
    { status: 'rejected', label: 'Decline', icon: 'close', class: 'btn btn-danger btn-sm', requiresNote: true },
  ]
  // ... existing accepted/in_progress/revision_requested branches unchanged
}
if (props.viewAs === 'company') {
  if (s === 'invited') return [
    { status: 'rejected', label: 'Withdraw Invite', icon: 'undo', class: 'btn btn-ghost btn-sm' },
  ]
  // ... existing pending/submitted/approved branches unchanged
}
```

The decline-note reuses the existing `noteFor` flow (same mechanism used today for `revision_requested`). Decline reason is recorded in `status_history[-1].note`.

### 8.7 `StatusBadge.vue`

Add an `invited` variant — teal/blue, visually distinct from `pending` (amber).

### 8.8 `ProfilePage.vue`

One additional button next to the existing "Edit" control, and mount the modal:

```vue
<button v-if="canInvite" class="btn btn-primary btn-sm" @click="showInvite = true">
  <span class="material-icons-round">person_add</span>Invite to Project
</button>
<InviteStudentModal v-model="showInvite" :studentId="user.id" />
```

Where `canInvite = auth.user?.role === 'company' && isStudent && !isMe`.

### 8.9 Company visibility

`CompanyAppsTab` and `ProjectBoardPage` already render everything in `byProject[projectId]`, so the new `invited` rows are included automatically. The drawer's `viewAs='company'` branch gets the new Withdraw action from §8.6. No other company-side changes required.

## 9. Notifications

In-app notifications are the **primary** channel. MongoDB-backed, already implemented, counter in Redis. Three new notification events:

| Event                   | Recipient  | Type    | Link            |
|-------------------------|------------|---------|-----------------|
| Company invites student | student    | invite  | `/applications` |
| Student accepts invite  | company    | info    | `/projects/:id` |
| Student declines invite | company    | info    | `/projects/:id` |
| Company withdraws invite| student    | info    | `/applications` |

All pushed via the existing `create_notification(user_id, title, message, type, link)` service.

## 10. Email (best-effort, optional)

A new email template `send_application_invite_email` is added to `src/core/email.py`, following the existing seven templates. The existing pattern in that module already gates every send on `SMTP_USER` and `SMTP_PASSWORD` being configured and logs without raising if they are missing. The new function follows the same pattern.

**Consequences:**

- The DigitalOcean deployment (which has outbound SMTP blocked and runs with `EMAIL_VERIFICATION_REQUIRED=false`, no `SMTP_USER`/`SMTP_PASSWORD`) does not send invite emails. It logs and moves on.
- The invite HTTP response never depends on email succeeding — the call is dispatched via `BackgroundTasks`, so even a transient SMTP failure has no effect on the request.
- Tests must not rely on the email being sent; they mock `send_application_invite_email` and assert it was scheduled on the `BackgroundTasks` object, not that it actually sent.

## 11. Testing

Backend, `backend/src/tests/`. In-memory SQLite + patched Redis / MongoDB / SMTP via the existing `conftest.py` fixtures.

### 11.1 New file — `test_invitations.py`

- `test_invite_student_happy_path` — company creates invite; DB row has `status=invited, initiator=company, cover_letter=<msg>`; notification mock called for student_id; email mock scheduled.
- `test_invite_non_student_rejected` — inviting a company/admin/committee → 400.
- `test_invite_not_project_owner` — different company tries to invite into someone else's project → 403.
- `test_invite_closed_project` — project `status != open` → 400.
- `test_invite_full_project` — `count_active >= max_participants` → 400.
- `test_invite_duplicate_blocked` — second invite for same `(project, student)` → 400.
- `test_student_accepts_invite` — student calls `PUT /:id/status {status: accepted}`, row transitions, `team_members` row created, project owner notified.
- `test_student_declines_invite_with_note` — decline with a note; `status_history[-1].note` is the decline reason; company notified.
- `test_company_withdraws_invite` — owner sets `invited → rejected`; student notified; re-invite to same project still blocked; re-invite to a different open project succeeds.
- `test_wrong_actor_rejected` — unrelated student cannot accept someone else's invite → 403.
- `test_invalid_transition` — `invited → in_progress` → 400.
- `test_email_not_required_for_invite_success` — `send_application_invite_email` mock raises; invite endpoint still returns 201 (proves background-task decoupling).

### 11.2 New file — `test_user_search.py`

- `test_search_requires_company_role` — student calling → 403.
- `test_search_by_skills_AND` — two skills, returns only students having both.
- `test_search_min_rating` — filters by `rating >= min_rating`.
- `test_search_available_excludes_active` — student in an `in_progress` application is excluded when `available=true`.
- `test_search_text_match` — `q=alice` matches on `username` and `full_name`.
- `test_search_pagination` — `page=2&size=5` returns the right slice and correct `total`.
- `test_search_cache_hit` — second identical call reads from Redis mock.

### 11.3 New file — `test_applications_migration_backfill.py`

- `test_existing_applications_default_to_student_initiator` — row created without `initiator` resolves to `student` on read.

### 11.4 `conftest.py` additions

- Add `send_application_invite_email` to `PATCHES` at both import sites (`src.core.email` and `src.applications.router`), matching the existing email-mock pattern.

### 11.5 Frontend

Per `CLAUDE.md`, the frontend has no test harness; the existing convention is manual UI verification. The implementation plan calls out manual checkpoints (company invites a student, student accepts and sees new team, student declines with note, company withdraws, re-invite to different project works) rather than introducing Vue test infra.

### 11.6 Test total

Suite goes from 93 → ~113 tests.

## 12. Rollout

Single deploy. The migration is additive; the enum addition is backward-compatible with existing data; no feature flag needed. After deploy:

- Existing applications behave identically.
- Companies see a new "Students" nav link and "Invite to Project" button on student profiles.
- Students see invites listed under "My Applications" with new accept/decline actions in the drawer.

## 13. Out of scope (future)

- Team invites to other companies / committees.
- Bulk invites and invitation templates.
- Invite expiry and auto-cancel.
- Student-side "looking for work" opt-in profile flag (if we ever decide derived availability isn't enough).
