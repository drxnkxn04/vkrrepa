# backend/apps/kpi/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.kpi.api import views

from apps.kpi.api.crossref_views import (
    CrossrefSyncView, CrossrefSearchByDoiView,
    CrossrefSearchView, CrossrefHealthCheckView
)


# Создаем роутер для ViewSets
router = DefaultRouter()

# Регистрация ViewSets
router.register(r'values', views.KpiValueViewSet, basename='kpivalue')
router.register(
    r'recommendations-list',
    views.RecommendationViewSet,
    basename='recommendation'
)

# URL-паттерны для приложения KPI
urlpatterns = [
    # === Маршруты из роутера ===
    # Включают автоматические маршруты для:
    # - /api/kpi/values/ (list, create, retrieve, update, delete)
    # - /api/kpi/values/dashboard/ (custom action)
    # - /api/kpi/values/history/ (custom action)
    # - /api/kpi/values/recommendations/ (custom action)
    # - /api/kpi/values/periods/ (custom action)
    # - /api/kpi/recommendations-list/ (list, retrieve)
    # - /api/kpi/recommendations-list/{id}/complete/ (custom action)
    path('', include(router.urls)),

    # === Список показателей для ручного ввода ===
    path(
        'indicators/manual/',
        views.ManualKpiIndicatorListView.as_view(),
        name='manual-kpi-indicators'
    ),

    # === Список всех групп KPI ===
    path(
        'groups/',
        views.KpiGroupListView.as_view(),
        name='kpi-groups'
    ),

    # === Дашборд руководителя ===
    path(
        'manager-dashboard/',
        views.ManagerDashboardView.as_view(),
        name='manager-dashboard'
    ),

    # === Топ сотрудников ===
    path(
        'top-performers/',
        views.TopPerformersView.as_view(),
        name='top-performers'
    ),

    # === Генерация PDF-отчета ===
    path(
        'reports/generate/',
        views.GenerateReportView.as_view(),
        name='generate-report'
    ),

    # === Синхронизация с Crossref ===
    path(
        'crossref/sync/',
        views.CrossrefSyncView.as_view(),
        name='crossref-sync'
    ),
        # Crossref интеграция
    path(
        'crossref/sync/',
        CrossrefSyncView.as_view(),
        name='crossref-sync'
    ),
    path(
        'crossref/search-by-doi/',
        CrossrefSearchByDoiView.as_view(),
        name='crossref-search-doi'
    ),
    path(
        'crossref/search/',
        CrossrefSearchView.as_view(),
        name='crossref-search'
    ),
    path(
        'crossref/health/',
        CrossrefHealthCheckView.as_view(),
        name='crossref-health'
    ),
]

"""
ПОЛНАЯ КАРТА API ЭНДПОИНТОВ:

=== Работа с KPI значениями ===
GET    /api/kpi/values/                    - Список значений KPI текущего пользователя
POST   /api/kpi/values/                    - Создание нового значения KPI
GET    /api/kpi/values/{id}/               - Получение конкретного значения
PUT    /api/kpi/values/{id}/               - Полное обновление значения
PATCH  /api/kpi/values/{id}/               - Частичное обновление значения
DELETE /api/kpi/values/{id}/               - Удаление значения

=== Дашборд и аналитика ===
GET    /api/kpi/values/dashboard/          - Данные для дашборда (основные KPI)
       Query params: ?period=YYYY-MM

GET    /api/kpi/values/history/            - История KPI за N месяцев
       Query params: ?months=6

GET    /api/kpi/values/periods/            - Список доступных периодов с данными

=== Рекомендации ===
GET    /api/kpi/values/recommendations/    - Персонализированные рекомендации
       Query params: ?period=YYYY-MM

GET    /api/kpi/recommendations-list/      - Список активных рекомендаций
GET    /api/kpi/recommendations-list/{id}/ - Конкретная рекомендация
POST   /api/kpi/recommendations-list/{id}/complete/ - Отметить как выполненную

=== Справочники ===
GET    /api/kpi/indicators/manual/         - Показатели для ручного ввода
GET    /api/kpi/groups/                    - Все группы KPI с показателями

=== Для руководителей (требуется is_staff=True) ===
GET    /api/kpi/manager-dashboard/         - Дашборд со всеми сотрудниками
       Query params: ?period=YYYY-MM

GET    /api/kpi/top-performers/            - Топ лучших сотрудников
       Query params: ?period=YYYY-MM&limit=10

=== Отчеты ===
GET    /api/kpi/reports/generate/          - Генерация PDF-отчета
       Query params: ?period=YYYY-MM (обязательный)
       Returns: PDF file

=== Интеграции ===
POST   /api/kpi/crossref/sync/             - Синхронизация публикаций из Crossref
       Body: {"orcid": "0000-0000-0000-0000", "year": 2024}

=== Формат данных ===

KpiValue:
{
    "id": 1,
    "indicator": {...},
    "period": "2024-12",
    "actual_value": 5.0,
    "target_value": 10.0,
    "is_verified": true,
    "evidence": "path/to/file.pdf",
    "comment": "Комментарий"
}

Dashboard response:
{
    "total_score": 85.5,
    "performance_level": "высокий",
    "bonus_amount": 25000.0,
    "group_scores": {
        "1": {
            "name": "Публикации",
            "score": 90.0,
            "indicators": [...]
        }
    },
    "period": "2024-12"
}

Recommendation:
{
    "id": 1,
    "indicator_name": "Публикации Scopus",
    "text": "Рекомендация...",
    "target_value": 5.0,
    "deadline_period": "2025-01",
    "current_completion": 60.0
}
"""