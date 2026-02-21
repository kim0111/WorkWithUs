# NexusHub Platform v2.0

Веб-платформа взаимодействия студентов, компаний и индустриального комитета.

## Архитектура

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Vue.js 3   │◄──►│  FastAPI     │◄──►│ PostgreSQL  │
│  Frontend   │    │  Backend     │    │ (основная)  │
│  :3000      │    │  :8000       │    │ :5432       │
└─────────────┘    │              │    └─────────────┘
                   │              │◄──►┌─────────────┐
                   │              │    │ MongoDB     │
                   │              │    │ (чат, логи) │
                   │              │    │ :27017      │
                   │              │    └─────────────┘
                   │              │◄──►┌─────────────┐
                   │              │    │ Redis       │
                   │              │    │ (кэш, ws)   │
                   │              │    │ :6379       │
                   │              │    └─────────────┘
                   │              │◄──►┌─────────────┐
                   │              │    │ MinIO       │
                   │              │    │ (файлы)     │
                   │              │    │ :9000/9001  │
                   └──────────────┘    └─────────────┘
```

## Технологии

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Backend** | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 | REST API, WebSocket |
| **Frontend** | Vue 3, Vue Router, Pinia, Axios, Vite | SPA |
| **PostgreSQL** | Основная БД | Пользователи, проекты, заявки, отзывы, файлы (мета) |
| **MongoDB** | NoSQL | Чат (сообщения, комнаты), уведомления, логи активности |
| **Redis** | Кэш/Pub-Sub | Кэширование, JWT blacklist, pub/sub для WebSocket, счётчики |
| **MinIO** | S3-совместимое хранилище | Файлы: ТЗ проектов, работы студентов, резюме, аватары |
| **JWT** | python-jose + passlib | Аутентификация, refresh-токены, blacklist через Redis |

## Структура бэкенда (Domain-based)

```
backend/app/
├── main.py              # FastAPI приложение, lifespan, CORS
├── core/
│   ├── config.py        # Pydantic Settings (все конфиги)
│   ├── security.py      # JWT: создание/валидация токенов, bcrypt
│   ├── dependencies.py  # get_current_user, require_role
│   ├── redis.py         # Redis: кэш, blacklist, pub/sub, rate-limit
│   ├── minio_client.py  # MinIO: upload/download/delete
│   └── email.py         # Gmail SMTP: шаблоны, BackgroundTasks
├── database/
│   ├── postgres.py      # AsyncEngine, Base, get_db
│   └── mongodb.py       # Motor client, indexes, get_mongodb
├── auth/                # Регистрация, логин, refresh, logout
│   ├── schemas.py
│   ├── service.py
│   └── router.py
├── users/               # Профили, навыки
│   ├── models.py        # User, CompanyProfile, StudentProfile
│   ├── schemas.py
│   ├── repository.py
│   ├── service.py
│   └── router.py
├── skills/              # Навыки (CRUD + кэш Redis)
│   ├── models.py
│   └── router.py
├── projects/            # Проекты (CRUD + фильтры + файлы)
│   ├── models.py        # Project, ProjectFile
│   └── router.py
├── applications/        # Заявки (8-этапный workflow)
│   └── router.py
├── chat/                # Чат WebSocket + REST + MongoDB + Redis pub/sub
│   └── router.py
├── files/               # Загрузка/скачивание файлов (MinIO)
│   └── router.py
├── notifications/       # Уведомления (MongoDB + Redis-счётчики)
│   └── router.py
├── reviews/             # Отзывы (двусторонние)
│   └── router.py
├── portfolio/           # Портфолио студентов
│   └── router.py
├── admin/               # Администрирование (статистика, блокировка)
│   └── router.py
└── tests/
    ├── conftest.py      # Fixtures, моки Redis/MongoDB/MinIO/SMTP
    ├── test_auth.py     # 14 тестов
    ├── test_users_projects.py  # 14 тестов
    └── test_features.py # 22 теста (workflow, reviews, portfolio, notif, admin)
```

## Workflow заявки (Application)

```
pending → accepted → in_progress → submitted → approved → completed
    ↓                                   ↓
 rejected                      revision_requested → submitted
```

- **Заказчик:** accept, reject, approve, revision_requested, complete
- **Исполнитель:** in_progress, submitted
- Двусторонние отзывы: заказчик → исполнитель И исполнитель → заказчик

## Где используется каждая БД

### PostgreSQL (реляционные данные)
- Пользователи, профили, навыки (M2M)
- Проекты, заявки, статусы
- Отзывы, рейтинги
- Портфолио
- Метаданные файлов (имя, размер, bucket, object_name)

### MongoDB (документы, высокая запись)
- **Chat messages** — вложенная структура, быстрая вставка
- **Chat rooms** — гибкая схема участников
- **Notifications** — переменная структура, массовые чтения
- **Activity logs** — аудит действий

### Redis (кэш, реал-тайм)
- **JWT Blacklist** — инвалидация токенов при logout
- **Cache** — список навыков, статистика админа, профили
- **Pub/Sub** — доставка сообщений чата между инстансами
- **Counters** — непрочитанные уведомления
- **Rate Limiting** — защита от спама

### MinIO (S3-файлы)
- `project-files` — ТЗ, документы к проектам
- `submissions` — работы студентов
- `avatars` — аватары пользователей
- `resumes` — резюме

## API Endpoints

| Модуль | Путь | Описание |
|--------|------|----------|
| Auth | `POST /auth/register` | Регистрация (student/company) |
| Auth | `POST /auth/login` | JWT-токены |
| Auth | `POST /auth/refresh` | Обновление токенов |
| Auth | `POST /auth/logout` | Logout + blacklist |
| Auth | `GET /auth/me` | Текущий пользователь |
| Users | `GET/PUT /users/{id}` | Профиль |
| Users | `POST/DELETE /users/{id}/skills/{id}` | Навыки |
| Skills | `GET/POST /skills/` | CRUD навыков |
| Projects | `GET/POST /projects/` | Список/создание |
| Projects | `GET/PUT/DELETE /projects/{id}` | Детали/редактирование |
| Applications | `POST /applications/` | Подать заявку |
| Applications | `PUT /applications/{id}/status` | Изменить статус |
| Applications | `GET /applications/my` | Мои заявки |
| Applications | `GET /applications/project/{id}` | Заявки проекта |
| Files | `POST /files/project/{id}` | Загрузка файла |
| Files | `GET /files/project/{id}` | Файлы проекта |
| Files | `GET /files/{id}/download` | Скачивание |
| Chat | `POST /chat/rooms/{project}/{user}` | Создать чат |
| Chat | `GET /chat/rooms` | Мои чаты |
| Chat | `GET /chat/rooms/{id}/messages` | История |
| Chat | `POST /chat/rooms/{id}/messages` | Отправить (REST) |
| Chat | `WS /chat/ws/{room_id}` | WebSocket |
| Notifications | `GET /notifications/` | Список |
| Notifications | `GET /notifications/unread-count` | Счётчик |
| Notifications | `PUT /notifications/{id}/read` | Прочитано |
| Reviews | `POST /reviews/` | Создать отзыв |
| Reviews | `GET /reviews/user/{id}` | Отзывы |
| Reviews | `GET /reviews/user/{id}/rating` | Рейтинг |
| Portfolio | `POST/GET/DELETE /portfolio/` | CRUD |
| Admin | `GET /admin/stats` | Статистика |
| Admin | `GET/PUT /admin/users` | Управление |

## Быстрый старт

```bash
# Запуск всех 6 сервисов
docker compose up --build

# Endpoints
# API:          http://localhost:8000
# Swagger:      http://localhost:8000/docs
# Frontend:     http://localhost:3000
# MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
```

## Тесты (50 тестов, ~80% coverage)

```bash
# Запуск тестов в контейнере
docker compose exec backend pytest app/tests/ -v --cov=app --cov-report=term-missing

# Или локально
cd backend
pip install -r requirements.txt
pytest app/tests/ -v --cov=app --cov-report=html
```

## Email (Gmail SMTP)

1. Включите "Двухэтапная аутентификация" в Google Account
2. Создайте "Пароль приложения" (App Password)
3. В `.env`:
```
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Структура frontend

```
frontend/src/
├── api/index.js       # Axios + interceptors
├── stores/            # Pinia: auth, toast
├── router/            # Vue Router + guards
├── components/        # Navbar, ProjectCard, ToastContainer
└── views/             # 11 страниц (Home, Login, Register, Dashboard,
                       #   Projects, ProjectDetail, CreateProject,
                       #   Profile, MyApplications, Notifications, Admin)
```
