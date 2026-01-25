# backend/vkrtry2/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Redirect с главной на API
    path('', RedirectView.as_view(url='/api/kpi/', permanent=False)),
    path('api/', RedirectView.as_view(url='/api/kpi/', permanent=False)),

    path('admin/', admin.site.urls),

    # JWT токены
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # KPI API
    path('api/kpi/', include('apps.kpi.urls')),
]