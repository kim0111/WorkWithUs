# NexusHub Platform — Diagrams Context

This document provides structured context for generating the five key architecture diagrams of the NexusHub platform (v2.0). Each section describes the elements, relationships, and notes needed to produce an accurate diagram.

---

## 1. System Architecture Diagram

**Purpose:** Show how the major runtime components communicate at deployment level.

### Components

| Layer | Component | Technology | Port |
|-------|-----------|------------|------|
| Client | Browser SPA | Vue 3 + Vite | — |
| Reverse Proxy | Caddy | Caddy v2 | 80 / 443 |
| API Server | FastAPI (async) | Python 3.12, Uvicorn | 8000 |
| Relational DB | PostgreSQL 16 | Tortoise ORM / asyncpg | 5435 (host) / 5432 (container) |
| Document DB | MongoDB 7 | Motor async driver | 27017 |
| Cache / Pub-Sub | Redis 7 | redis-py async | 6379 |
| Object Storage | MinIO | minio Python SDK | 9000 (API) / 9001 (console) |
| Email | Gmail SMTP | aiosmtplib | 587 |

### Communication paths

```
Browser
  ──HTTP/HTTPS──►  Caddy
                     ├──proxy /api/*──►  FastAPI (8000)
                     │                      ├── Tortoise ORM ──► PostgreSQL
                     │                      ├── Motor         ──► MongoDB
                     │                      ├── redis-py      ──► Redis
                     │                      └── MinIO SDK     ──► MinIO
                     └──proxy /*──►  Vite static files (3000 in dev)

Browser ──WebSocket (ws://host/api/v1/chat/ws/{roomId})──► FastAPI
FastAPI ──pub/sub──► Redis (chat fan-out between server instances)
FastAPI ──BackgroundTask──► Gmail SMTP (email notifications)
```

### Key design decisions
- No API Gateway — Caddy terminates TLS and routes by path prefix.
- All FastAPI DB access is async; no synchronous drivers used.
- Redis serves three roles: JWT blacklist, response cache (skills/stats/profiles), and WebSocket pub/sub channel for chat rooms.
- MinIO buckets: `avatars`, `project-files`, `submissions`, `resumes`.
- Docker Compose orchestrates all services in a single network; production uses `docker-compose.prod.yml` + Caddy.

---

## 2. ERD Diagram (Entity-Relationship Diagram)

**Storage split:** PostgreSQL holds all relational entities below. MongoDB holds chat rooms, chat messages, notifications, and activity logs (schema-less, high write-throughput).

### PostgreSQL Entities

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| email | varchar(255) | unique, indexed |
| username | varchar(100) | unique, indexed |
| hashed_password | varchar(255) | |
| full_name | varchar(255) | nullable |
| role | enum | student / company / committee / admin |
| avatar_url | varchar(500) | nullable |
| bio | text | nullable |
| is_active | bool | default true |
| is_blocked | bool | default false |
| created_at | datetime | auto |
| updated_at | datetime | auto |

#### `student_profiles`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| user_id | FK → users | 1-to-1, cascade delete |
| university | varchar(255) | nullable |
| major | varchar(255) | nullable |
| graduation_year | int | nullable |
| gpa | float | nullable |
| resume_url | varchar(500) | nullable |
| rating | float | default 0.0 |
| completed_projects_count | int | default 0 |

#### `company_profiles`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| user_id | FK → users | 1-to-1, cascade delete |
| company_name | varchar(255) | |
| industry | varchar(255) | nullable |
| website | varchar(500) | nullable |
| description | text | nullable |
| location | varchar(255) | nullable |

#### `skills`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| name | varchar(100) | unique |
| category | varchar(100) | nullable |

#### `user_skills` (M2M join)
| Column | Type |
|--------|------|
| user_id | FK → users |
| skill_id | FK → skills |

#### `projects`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| title | varchar(255) | |
| description | text | |
| owner_id | FK → users | cascade delete |
| status | enum | open / in_progress / closed |
| max_participants | int | default 1 |
| deadline | datetime | nullable |
| is_student_project | bool | default false |
| created_at | datetime | auto |
| updated_at | datetime | auto |

#### `project_skills` (M2M join)
| Column | Type |
|--------|------|
| project_id | FK → projects |
| skill_id | FK → skills |

#### `project_files`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| project_id | FK → projects | cascade delete |
| uploader_id | FK → users | cascade delete |
| filename | varchar(500) | |
| object_name | varchar(500) | MinIO key |
| file_size | int | nullable |
| content_type | varchar(255) | nullable |
| file_type | varchar(50) | default "attachment" |
| created_at | datetime | auto |

#### `applications`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| project_id | FK → projects | cascade delete |
| applicant_id | FK → users | cascade delete |
| cover_letter | text | nullable |
| status | enum | invited / pending / accepted / rejected / in_progress / submitted / revision_requested / approved / completed |
| initiator | enum | student / company |
| submission_note | text | nullable |
| revision_note | text | nullable |
| status_history | JSON | audit log array |
| created_at | datetime | auto |
| updated_at | datetime | auto |
Unique constraint: (project_id, applicant_id)

#### `reviews`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| reviewer_id | FK → users | cascade delete |
| reviewee_id | FK → users | cascade delete |
| project_id | FK → projects | cascade delete |
| application_id | FK → applications | nullable, cascade delete |
| rating | float | |
| comment | text | nullable |
| review_type | varchar(50) | nullable |
| created_at | datetime | auto |

#### `portfolio_items`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| student_id | FK → student_profiles | cascade delete |
| title | varchar(255) | |
| description | text | nullable |
| project_url | varchar(500) | nullable |
| image_url | varchar(500) | nullable |
| created_at | datetime | auto |

#### `project_teams`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| project_id | FK → projects | cascade delete |
| user_id | FK → users | cascade delete |
| role | enum | lead / frontend / backend / designer / pm / qa / other |
| is_lead | bool | default false |
| joined_at | datetime | auto |
Unique constraint: (project_id, user_id)

#### `tasks`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| project_id | FK → projects | cascade delete |
| title | varchar(255) | |
| description | text | |
| status | enum | todo / in_progress / review / done |
| priority | enum | low / medium / high |
| assignee_id | FK → users | nullable, SET NULL |
| deadline | datetime | nullable |
| created_by_id | FK → users | cascade delete |
| created_at | datetime | auto |
| updated_at | datetime | auto |

#### `task_comments`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| task_id | FK → tasks | cascade delete |
| author_id | FK → users | cascade delete |
| content | text | |
| created_at | datetime | auto |

#### `task_activities`
| Column | Type | Notes |
|--------|------|-------|
| id | PK int | |
| task_id | FK → tasks | cascade delete |
| actor_id | FK → users | cascade delete |
| action | varchar(50) | |
| from_value | varchar(255) | nullable |
| to_value | varchar(255) | nullable |
| created_at | datetime | auto |

### MongoDB Collections (schema reference)

| Collection | Key fields |
|------------|-----------|
| `chat_rooms` | `_id`, `name`, `participants[]` (user ids), `project_id`, `created_at` |
| `chat_messages` | `_id`, `room_id`, `sender_id`, `content`, `created_at` |
| `notifications` | `_id`, `user_id`, `title`, `message`, `type`, `link`, `is_read`, `created_at` |
| `activity_logs` | `_id`, `user_id`, `action`, `entity_type`, `entity_id`, `created_at` |

---

## 3. Use Case Diagram

**Actors:**
- **Student** — registers, browses projects, applies or accepts invites, works on projects, chats, submits work, gets reviewed, builds portfolio.
- **Company** — registers, creates projects, reviews applications, invites students, manages team/tasks, reviews submitted work, leaves reviews.
- **Committee** — oversees platform, approves/rejects final submissions, monitors activity.
- **Admin** — full platform access: block/unblock users, manage skills, view platform stats.
- **System** (automated) — sends email notifications, generates real-time WebSocket messages, caches data in Redis.

### Use Cases by Actor

#### Student
- Register / Login / Logout
- Verify email
- Edit profile (avatar, bio, skills, university info)
- Browse & search projects (filter by skill, status)
- Apply to a project (submit cover letter)
- Accept / Decline company invitation
- Track my applications (status timeline)
- Submit work on an accepted application
- Request revision acknowledgement
- Chat in project chat room
- Receive notifications (real-time + email)
- View & manage portfolio items
- Leave review for company after project completion

#### Company
- Register / Login / Logout
- Edit company profile
- Create / Edit / Delete project
- Browse student profiles (search by skill, university)
- Invite student to project
- Accept / Reject student application
- Request revision on submitted work
- Approve / Complete student work
- Manage project team (assign roles, mark lead)
- Create / Assign / Move tasks on project Kanban board
- Comment on tasks
- Chat in project chat room
- Leave review for student after project completion

#### Committee
- Login / Logout
- Browse all projects and applications
- Approve or reject submitted work (final authority)
- View platform activity logs

#### Admin
- Login / Logout
- View platform statistics (users, projects, applications counts)
- Block / Unblock users
- Create / Edit / Delete skills taxonomy
- Promote user to different role

#### System (automated)
- Send email: verification, welcome, application status change, new application, submission, invite, chat notification, review
- Deliver real-time WebSocket events (chat messages)
- Publish Redis pub/sub for chat fan-out
- Cache skills list and user profiles in Redis

---

## 4. Activity Diagram

**Primary flow: Student applies to a project and completes it.**

```
[Student] Browses Projects
       │
       ▼
[Student] Submits Application (cover letter)
       │
       ▼
       ╔═══════════════════════════════╗
       ║ [System] Notifies Company     ║  (email + in-app)
       ╚═══════════════════════════════╝
       │
       ▼
[Company] Reviews Application
       │
       ├── REJECT ──► [System] Sends rejection email ──► END
       │
       └── ACCEPT
              │
              ▼
       Status → accepted
              │
              ▼
       [Student] Works on project
              │  (chat, tasks, file uploads)
              │
              ▼
       [Student] Submits work (submission_note)
              │
              ▼
       ╔═══════════════════════════════╗
       ║ [System] Notifies Company     ║
       ╚═══════════════════════════════╝
              │
              ▼
       [Company] Reviews Submission
              │
              ├── REQUEST REVISION
              │       │
              │       ▼
              │   [Student] Reworks ──► re-submits (loop back)
              │
              └── APPROVE
                     │
                     ▼
              Status → approved
                     │
                     ▼
              [Company/Committee] Marks Complete
                     │
                     ▼
              Status → completed
                     │
                     ├── [Company] Leaves review for Student
                     └── [Student] Leaves review for Company
                                   │
                                   ▼
                            [System] Updates student rating & portfolio
```

**Secondary flow: Company invites a Student.**

```
[Company] Finds Student on Students search page
       │
       ▼
[Company] Sends Invite (selects project + message)
       │
       ▼
Application created with status = "invited", initiator = "company"
       │
       ▼
[System] Sends invite email + in-app notification to Student
       │
       ▼
[Student] Views invite in "My Applications"
       │
       ├── DECLINE ──► status = rejected ──► END
       │
       └── ACCEPT
              │
              ▼
       status = accepted
              │
              ▼  (continues same as standard application flow above from "accepted")
```

**Task Kanban flow (within an in-progress project):**

```
[Company] Creates Task (title, description, priority, assignee, deadline)
       │
       ▼
Task status = todo
       │
       ▼
[Assignee/Company] Moves task → in_progress
       │
       ▼
[Assignee] Moves task → review
       │
       ▼
[Company/Lead] Approves → done
                        OR requests changes → back to in_progress
```

### Application Status State Machine

```
                invited (company-initiated)
                   │
        accept     │      decline
    ┌──────────────┘──────────────┐
    │                             │
    ▼                             ▼
 pending (student-initiated)   rejected
    │
    ├── reject ──────────────────► rejected
    │
    └── accept
           │
           ▼
        accepted
           │
           └── submit
                  │
                  ▼
               submitted
                  │
                  ├── revision_requested ──► (student re-submits) ──► submitted
                  │
                  └── approved
                         │
                         └── completed
```

---

## 5. Project Structure Diagram

```
student-company-platform-work/
├── docker-compose.yml           # Dev orchestration (all 6 services)
├── docker-compose.prod.yml      # Production with Caddy TLS
├── CLAUDE.md                    # AI assistant codebase guide
├── DEPLOY.md
├── README.md
├── ROADMAP.md
│
├── caddy/
│   └── Caddyfile                # Reverse proxy config
│
├── docs/
│   └── diagrams-context.md      # ← this file
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml           # Aerich migration config
│   ├── .env                     # Secrets (not committed)
│   │
│   ├── migrations/
│   │   └── models/              # Aerich migration files
│   │
│   └── src/
│       ├── main.py              # FastAPI app, lifespan, router mounting
│       │
│       ├── core/
│       │   ├── config.py        # Pydantic BaseSettings (env vars)
│       │   ├── dependencies.py  # get_current_user, require_role
│       │   ├── security.py      # JWT encode/decode, password hashing
│       │   ├── email.py         # aiosmtplib email dispatchers
│       │   ├── redis.py         # Redis async client & helpers
│       │   ├── minio_client.py  # MinIO SDK client & bucket helpers
│       │   └── activity.py      # Activity log writer (MongoDB)
│       │
│       ├── database/
│       │   ├── postgres.py      # Tortoise ORM init/close
│       │   └── mongodb.py       # Motor client init/close
│       │
│       ├── auth/                # JWT login, register, refresh, logout
│       ├── users/               # User CRUD, profile management, search
│       ├── skills/              # Skills taxonomy (CRUD, caching)
│       ├── projects/            # Project CRUD, discovery, filtering
│       ├── applications/        # Apply, invite, status workflow, history
│       ├── files/               # File upload/download via MinIO
│       ├── chat/                # WebSocket rooms, message history (MongoDB)
│       ├── notifications/       # In-app notifications (MongoDB + Redis counter)
│       ├── reviews/             # Mutual reviews after project completion
│       ├── portfolio/           # Student portfolio items
│       ├── teams/               # Project team membership & roles
│       ├── tasks/               # Kanban tasks, comments, activity log
│       └── admin/               # Admin stats, user management, skill management
│           # Each domain module contains:
│           #   __init__.py
│           #   models.py     — Tortoise ORM models (PostgreSQL)
│           #   schemas.py    — Pydantic request/response schemas
│           #   router.py     — FastAPI APIRouter with endpoints
│           #   service.py    — Business logic layer
│           #   repository.py — DB query helpers
│
│       └── tests/
│           ├── conftest.py      # SQLite in-memory DB, all external service mocks
│           ├── test_auth.py
│           ├── test_users_projects.py
│           ├── test_features.py
│           ├── test_applications_history.py
│           ├── test_invitations.py
│           ├── test_discovery.py
│           ├── test_tasks.py
│           ├── test_teams.py
│           └── test_user_search.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js           # Proxy /api → localhost:8000
    │
    └── src/
        ├── main.js              # Vue app bootstrap, Pinia, Router
        ├── App.vue              # Root component, ToastContainer
        │
        ├── api/
        │   └── index.js         # Axios instance, JWT injection, 401 refresh
        │
        ├── router/
        │   └── index.js         # Routes with requiresAuth / guest / admin guards
        │
        ├── stores/              # Pinia state management
        │   ├── auth.js          # User session, login/logout/refresh
        │   ├── projects.js      # Project list, detail, create
        │   ├── applications.js  # myApps, byProject, status mutations
        │   ├── notifications.js # Unread count, list
        │   ├── tasks.js         # Kanban board state
        │   ├── teams.js         # Project team members
        │   ├── theme.js         # Dark/light mode
        │   └── toast.js         # Toast notification queue
        │
        ├── components/          # Shared primitives
        │   ├── AppNavbar.vue
        │   ├── BaseModal.vue
        │   ├── BaseTabs.vue
        │   ├── BasePagination.vue
        │   ├── StatusBadge.vue
        │   ├── EmptyState.vue
        │   ├── FormField.vue
        │   ├── ConfirmDialog.vue
        │   ├── SkillPicker.vue
        │   ├── SkeletonBlock.vue
        │   ├── FileUpload.vue
        │   ├── ToastContainer.vue
        │   ├── ProjectCard.vue
        │   ├── ProjectTeamPanel.vue
        │   ├── TaskCard.vue
        │   ├── TaskDetailDrawer.vue
        │   ├── ApplicationTimeline.vue
        │   ├── ApplicationDetailDrawer.vue
        │   ├── InviteStudentModal.vue
        │   │
        │   ├── dashboard/
        │   │   ├── DashboardStudentSection.vue
        │   │   └── DashboardCompanySection.vue
        │   │
        │   └── profile/
        │       ├── StudentInfoGrid.vue
        │       ├── StudentAppsTab.vue
        │       ├── StudentPortfolioTab.vue
        │       ├── CompanyInfoGrid.vue
        │       ├── CompanyProjectsTab.vue
        │       ├── CompanyAppsTab.vue
        │       ├── EditProfileModal.vue
        │       └── ReviewsTab.vue
        │
        └── views/               # Route-level page components
            ├── HomePage.vue
            ├── LoginPage.vue
            ├── RegisterPage.vue
            ├── VerifyEmailPage.vue
            ├── DashboardPage.vue    # Dispatches to role-specific section
            ├── ProfilePage.vue      # Dispatches to role-specific tabs
            ├── ProjectsPage.vue
            ├── ProjectDetailPage.vue
            ├── ProjectBoardPage.vue # Kanban board
            ├── CreateProjectPage.vue
            ├── StudentsPage.vue     # Company: search & invite students
            ├── MyApplicationsPage.vue
            ├── ChatListPage.vue
            ├── ChatRoomPage.vue     # WebSocket real-time chat
            ├── NotificationsPage.vue
            ├── AdminPage.vue
            └── NotFoundPage.vue
```

### Route → Role access matrix

| Route | Guest | Student | Company | Committee | Admin |
|-------|-------|---------|---------|-----------|-------|
| `/` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/projects` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/projects/:id` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/login`, `/register` | ✓ | redirect | redirect | redirect | redirect |
| `/dashboard` | redirect | ✓ | ✓ | ✓ | ✓ |
| `/profile/:id` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/projects/create` | ✗ | ✗ | ✓ | ✗ | ✓ |
| `/projects/:id/board` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `/my-applications` | ✗ | ✓ | ✗ | ✗ | ✗ |
| `/students` | ✗ | ✗ | ✓ | ✗ | ✓ |
| `/chat`, `/chat/:id` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `/notifications` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `/admin` | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Diagram Tool Recommendations

| Diagram | Recommended tool |
|---------|-----------------|
| System Architecture | draw.io (C4 Context/Container level), Lucidchart, or Mermaid `graph TD` |
| ERD | draw.io, dbdiagram.io, or Mermaid `erDiagram` |
| Use Case | draw.io, PlantUML `@startuml usecase`, or Lucidchart |
| Activity / State Machine | PlantUML `@startuml activity` / `@startuml state`, or Mermaid `stateDiagram-v2` |
| Project Structure | Plain tree (as above), or VS Code file tree screenshot |
