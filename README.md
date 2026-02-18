# Веб-платформа взаимодействия студентов, компаний и индустриального комитета

## Технологии

- **Backend:** FastAPI, SQLAlchemy (async), PostgreSQL, JWT, Alembic
- **Frontend:** Vue 3 (Composition API), Vue Router, Pinia, Axios, Vite
- **Инфраструктура:** Docker, Docker Compose

## Быстрый старт

```bash
# Запуск всей системы
docker compose up --build

# API доступен на http://localhost:8000
# Swagger-документация: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── core/
│   │   ├── config.py        # Настройки приложения
│   │   └── security.py      # JWT, хеширование паролей
│   ├── database/
│   │   ├── session.py       # Подключение к БД
│   │   └── deps.py          # Зависимости
│   ├── models/
│   │   └── models.py        # SQLAlchemy модели
│   ├── schemas/
│   │   └── schemas.py       # Pydantic схемы
│   ├── repositories/
│   │   └── repositories.py  # Слой доступа к данным
│   ├── services/
│   │   └── services.py      # Бизнес-логика
│   └── api/
│       ├── deps.py           # Auth-зависимости
│       └── routes/            # Эндпоинты API
├── alembic/                   # Миграции БД
├── tests/                     # Тесты
├── Dockerfile
└── requirements.txt
```

## API Endpoints

| Группа | Путь | Описание |
|--------|------|----------|
| Auth | `/api/v1/auth/` | Регистрация, вход, refresh токен |
| Users | `/api/v1/users/` | Профили, навыки |
| Projects | `/api/v1/projects/` | CRUD проектов, фильтрация, пагинация |
| Applications | `/api/v1/applications/` | Отклики на проекты |
| Portfolio | `/api/v1/portfolio/` | Портфолио студентов |
| Reviews | `/api/v1/reviews/` | Отзывы и рейтинг |
| Skills | `/api/v1/skills/` | Управление навыками |
| Notifications | `/api/v1/notifications/` | Уведомления |
| Admin | `/api/v1/admin/` | Админ-панель, статистика |

## Роли

- **student** — просмотр проектов, отклики, портфолио
- **company** — создание проектов, управление откликами
- **committee** — индустриальный комитет
- **admin** — полный доступ, модерация

## Тестирование

```bash
cd backend
pip install aiosqlite
pytest tests/ -v
```

## Миграции (Alembic)

```bash
# Внутри контейнера backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
