# backend/apps/kpi/admin.py

from django.contrib import admin
from .models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation, UserProfile

admin.site.register(KpiGroup)
admin.site.register(KpiIndicator)
admin.site.register(KpiValue)
admin.site.register(KpiRecommendation)
admin.site.register(UserProfile)  # ⚠️ ДОБАВЛЕНО