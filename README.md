# Программа управления ключевыми показателями эффективности сотрудников центра ИИ

Веб-программа для управления ключевыми показателями эффективности (KPI) сотрудников центра. Позволяет вводить, отслеживать, утверждать показатели, генерировать отчёты и персональные рекомендации.

## Стек технологий

| Компонент   | Технологии                                           |
|-------------|------------------------------------------------------|
| Backend     | Python 3.12, Django 5, Django REST Framework         |
| Frontend    | Vue 3, Vuex 4, Vue Router 4, Chart.js               |
| БД          | PostgreSQL 16                                        |
| Кэш         | Redis (prod) / LocMemCache (dev)                    |
| Очереди     | Celery 5 + Redis                                     |
| Отчёты      | ReportLab (PDF), OpenPyXL (Excel)                    |
| Аутентификация | JWT (Simple JWT)                                  |
| Документация API | drf-spectacular (OpenAPI 3, Swagger UI)          |

## Функциональность

- Персональный дашборд с графиками динамики KPI
- Ввод фактических значений с прикреплением подтверждающих документов
- Workflow согласования: черновик -> на проверке -> подтверждено / отклонено
- Дашборд руководителя: рейтинг, фильтрация, массовое утверждение/отклонение
- Генерация PDF и Excel отчётов
- Персональные рекомендации при низких показателях
- Интеграция с Crossref API (импорт научных публикаций по ORCID)
- Система уведомлений
- Профиль пользователя с аватаром и ORCID
- Аудит-лог всех изменений значений KPI
- Ролевая модель: ППС (профессорско-преподавательский состав) и РОП (руководитель)

## Быстрый старт

### Предварительные требования

- Python 3.12
- Node.js 18+
- PostgreSQL 14+
- Redis (опционально, для prod-режима и Celery)

### 1. Клонирование

```bash
git clone <url-репозитория>
cd vkrrepa-main_project
```

### 2. Backend

```bash
cd backend

# Виртуальное окружение
python -m venv .venv
.venv\Scripts\activate   # Windows

# Зависимости
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env: укажите DJANGO_SECRET_KEY и данные БД

# База данных
python manage.py migrate

# Начальная структура KPI (группы и показатели)
python manage.py init_kpi_structure

# Профили пользователей (создать для существующих users)
python manage.py create_user_profiles

# Демо-данные (опционально — тестовые пользователи и заполненные KPI)
python manage.py populate_test_data
python manage.py prepare_demo_workflow

# Запуск сервера
python manage.py runserver
```

### 3. Frontend

```bash
cd frontend

# Настройка окружения
cp .env.example .env

# Зависимости
npm install

# Запуск dev-сервера
npm run serve
```

Приложение будет доступно по адресу `http://localhost:8080`.

## Конфигурация

### Переменные окружения (backend/.env)

| Переменная                    | Описание                           | По умолчанию     |
|-------------------------------|------------------------------------|-------------------|
| `DJANGO_SECRET_KEY`           | Секретный ключ Django              | -                 |
| `DJANGO_DEBUG`                | Режим отладки                      | `false`           |
| `DJANGO_ALLOWED_HOSTS`        | Разрешённые хосты                  | `localhost`       |
| `DJANGO_CORS_ALLOW_ALL_ORIGINS` | Разрешить все источники (dev)    | `true`            |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Белый список источников (prod)     | `http://localhost:8080` |
| `DB_NAME`                     | Имя базы данных                    | `kpi_db`          |
| `DB_USER`                     | Пользователь БД                    | `postgres`        |
| `DB_PASSWORD`                 | Пароль БД (обязателен)             | -                 |
| `DB_HOST`                     | Хост БД                            | `localhost`       |
| `DB_PORT`                     | Порт БД                            | `5432`            |
| `KPI_BASE_SALARY`             | Базовый оклад для расчёта премии   | `50000`           |
| `CROSSREF_MAILTO`             | Email для Crossref API             | -                 |
| `CROSSREF_USER_AGENT`         | User-Agent для Crossref API        | -                 |

### Переменные окружения (frontend/.env)

| Переменная               | Описание           | По умолчанию                  |
|--------------------------|--------------------|-------------------------------|
| `VUE_APP_API_URL`        | URL backend API    | `http://127.0.0.1:8000`      |
| `VUE_APP_TITLE`          | Заголовок приложения | `KPI Management System`     |

## Структура проекта

```
backend/
  apps/kpi/
    models.py              # Модели: KpiGroup, KpiIndicator, KpiValue и др.
    api/views.py           # REST API endpoints
    services/
      kpi_calculator.py    # Бизнес-логика расчётов
      report_generator.py  # Генерация PDF/Excel
    tasks.py               # Celery-задачи
    tests/                 # Тесты (9 модулей)
  apps/integrations/       # Интеграция с Crossref API
  vkrtry2/settings.py      # Настройки Django

frontend/src/
  views/                   # Страницы (Dashboard, History, Manager и др.)
  components/              # Переиспользуемые компоненты
  services/api.js          # API-клиент (Axios)
  store/index.js           # Vuex хранилище
  router/index.js          # Маршруты
```

## API

### Интерактивная документация

После запуска backend доступны:

- `http://localhost:8000/api/docs/` — Swagger UI
- `http://localhost:8000/api/redoc/` — ReDoc
- `http://localhost:8000/api/schema/` — OpenAPI 3 схема (YAML)

### Основные группы endpoints

- `POST /api/token/` — получение JWT-токена
- `POST /api/token/refresh/` — обновление токена
- `GET/POST /api/kpi/values/` — CRUD значений KPI
- `POST /api/kpi/values/{id}/submit/` — отправка на проверку
- `POST /api/kpi/values/{id}/approve/` — утверждение (руководитель)
- `POST /api/kpi/values/{id}/reject/` — отклонение (руководитель)
- `GET /api/kpi/values/dashboard/` — данные дашборда
- `GET /api/kpi/values/history/` — история KPI
- `GET /api/kpi/manager-dashboard/` — дашборд руководителя
- `GET /api/kpi/reports/generate/` — генерация PDF-отчёта
- `GET /api/kpi/reports/generate-excel/` — генерация Excel-отчёта
- `GET /api/kpi/profile/` — профиль пользователя
- `GET /api/kpi/notifications/` — уведомления
- `POST /api/kpi/crossref/sync/` — импорт публикаций из Crossref

## Тестирование

```bash
cd backend
python manage.py test apps.kpi.tests -v 2
```

## Лицензия

Учебный проект. Бакалаврская работа.
