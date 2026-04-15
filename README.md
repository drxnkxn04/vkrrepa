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

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

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

# Демо-данные (опционально)
python manage.py shell -c "
from apps.kpi.management.commands import create_demo_data
"

# Запуск сервера
python manage.py runserver
```

### 3. Frontend

```bash
cd frontend

# Зависимости
npm install

# Запуск dev-сервера
npm run serve
```

Приложение будет доступно по адресу `http://localhost:5173`.

## Конфигурация

### Переменные окружения (backend/.env)

| Переменная                    | Описание                           | По умолчанию     |
|-------------------------------|------------------------------------|-------------------|
| `DJANGO_SECRET_KEY`           | Секретный ключ Django              | -                 |
| `DJANGO_DEBUG`                | Режим отладки                      | `false`           |
| `DJANGO_ALLOWED_HOSTS`        | Разрешённые хосты                  | `localhost`       |
| `DB_NAME`                     | Имя базы данных                    | `vkrtry2`         |
| `DB_USER`                     | Пользователь БД                    | `postgres`        |
| `DB_PASSWORD`                 | Пароль БД                          | -                 |
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

Основные группы endpoints:

- `POST /api/token/` — получение JWT-токена
- `GET/POST /api/kpi/values/` — CRUD значений KPI
- `POST /api/kpi/values/{id}/submit/` — отправка на проверку
- `POST /api/kpi/values/{id}/approve/` — утверждение (руководитель)
- `POST /api/kpi/values/{id}/reject/` — отклонение (руководитель)
- `GET /api/kpi/values/dashboard/` — данные дашборда
- `GET /api/kpi/values/history/` — история KPI
- `GET /api/kpi/manager-dashboard/` — дашборд руководителя
- `GET /api/kpi/reports/generate/` — генерация отчётов
- `GET /api/kpi/profile/` — профиль пользователя
- `GET /api/kpi/notifications/` — уведомления

## Тестирование

```bash
cd backend
python manage.py test apps.kpi.tests -v 2
```

## Лицензия

Учебный проект. Бакалаврская работа.
