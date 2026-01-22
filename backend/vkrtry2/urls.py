# backend/vkrtry2/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
# ↓↓↓ ЭТИ ДВЕ СТРОКИ НЕОБХОДИМО ДОБАВИТЬ:
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def api_root(request):
    """Корневой эндпоинт API с информацией о доступных маршрутах"""
    return JsonResponse({
        'message': 'KPI Management System API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'token_obtain': '/api/token/',
            'token_refresh': '/api/token/refresh/',
            'kpi_api': '/api/kpi/',
            'available_endpoints': {
                'groups': '/api/kpi/groups/',
                'indicators_manual': '/api/kpi/indicators/manual/',
                'dashboard': '/api/kpi/values/dashboard/?period=YYYY-MM',
                'history': '/api/kpi/values/history/?months=6',
                'recommendations': '/api/kpi/values/recommendations/?period=YYYY-MM',
                'manager_dashboard': '/api/kpi/manager-dashboard/?period=YYYY-MM',
                'generate_report': '/api/kpi/reports/generate/?period=YYYY-MM',
            }
        },
        'documentation': 'Contact developer for API documentation'
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    # ↓↓↓ ИСПРАВЛЕННЫЕ СТРОКИ:
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/kpi/', include('apps.kpi.urls')),
]
