# backend/apps/kpi/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.kpi.api import views
from apps.kpi.api.profile_views import UserProfileView, ChangePasswordView, AvatarUploadView

from apps.kpi.api.crossref_views import (
    CrossrefSyncView, CrossrefSearchByDoiView,
    CrossrefSearchView, CrossrefSaveToKpiView,
    CrossrefHealthCheckView,
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
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'targets', views.KpiTargetViewSet, basename='kpitarget')

# URL-паттерны для приложения KPI
urlpatterns = [
    # === Маршруты из роутера ===
    path('', include(router.urls)),

    # === Профиль пользователя ===
    path(
        'profile/',
        UserProfileView.as_view(),
        name='user-profile'
    ),
    path(
        'profile/change-password/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    path(
        'profile/avatar/',
        AvatarUploadView.as_view(),
        name='avatar-upload'
    ),

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

    # === Среднее по команде ===
    path(
        'team-average/',
        views.TeamAverageView.as_view(),
        name='team-average'
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
    path(
        'reports/generate/<int:user_id>/',
        views.GenerateUserReportView.as_view(),
        name='generate-user-report'
    ),

    # === Генерация Excel-отчета ===
    path(
        'reports/generate-excel/',
        views.GenerateExcelReportView.as_view(),
        name='generate-excel-report'
    ),
    path(
        'reports/generate-excel/<int:user_id>/',
        views.GenerateUserExcelReportView.as_view(),
        name='generate-user-excel-report'
    ),

    # === Сводные отчёты ===
    path(
        'reports/summary/',
        views.GenerateSummaryReportView.as_view(),
        name='generate-summary-report'
    ),
    path(
        'reports/summary-excel/',
        views.GenerateSummaryExcelView.as_view(),
        name='generate-summary-excel'
    ),

    # === Синхронизация с Crossref ===
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
        'crossref/save-to-kpi/',
        CrossrefSaveToKpiView.as_view(),
        name='crossref-save-to-kpi'
    ),
    path(
        'crossref/health/',
        CrossrefHealthCheckView.as_view(),
        name='crossref-health'
    ),
]
