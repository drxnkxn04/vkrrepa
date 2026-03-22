# backend/apps/kpi/admin.py

from django.contrib import admin
from .models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation, UserProfile


@admin.register(KpiGroup)
class KpiGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'weight', 'max_points', 'min_threshold', 'order')
    list_filter = ('role',)
    ordering = ('role', 'order')


@admin.register(KpiIndicator)
class KpiIndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'max_value', 'max_points', 'weight', 'unit', 'data_source', 'order')
    list_filter = ('group__role', 'data_source', 'group')
    search_fields = ('name',)
    ordering = ('group__role', 'group__order', 'order')


@admin.register(KpiValue)
class KpiValueAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'indicator',
        'period',
        'actual_value',
        'target_value',
        'status',
        'is_verified',
        'reviewer',
        'reviewed_at',
    )
    list_filter = ('status', 'is_verified', 'period', 'indicator__group__role')
    search_fields = ('user__username', 'indicator__name', 'comment')


@admin.register(KpiRecommendation)
class KpiRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'indicator', 'period', 'priority', 'current_completion', 'is_completed')
    list_filter = ('priority', 'is_completed', 'period')
    search_fields = ('user__username', 'indicator__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'orcid', 'department', 'position')
    list_filter = ('role',)
    search_fields = ('user__username', 'orcid')
