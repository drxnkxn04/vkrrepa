# backend/apps/kpi/admin.py

from django.contrib import admin
from .models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation, UserProfile


@admin.register(KpiValue)
class KpiValueAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'indicator',
        'period',
        'status',
        'is_verified',
        'reviewer',
        'reviewed_at',
    )
    list_filter = ('status', 'is_verified', 'period')
    search_fields = ('user__username', 'indicator__name', 'comment')

admin.site.register(KpiGroup)
admin.site.register(KpiIndicator)
admin.site.register(KpiRecommendation)
admin.site.register(UserProfile)