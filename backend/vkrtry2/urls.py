from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenRefreshView
from apps.kpi.jwt_serializer import CustomTokenObtainPairSerializer  # НОВЫЙ ИМПОРТ
from rest_framework_simplejwt.views import TokenObtainPairView

# Кастомный view с нашим serializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('', RedirectView.as_view(url='/api/kpi/', permanent=False)),
    path('api/', RedirectView.as_view(url='/api/kpi/', permanent=False)),
    path('admin/', admin.site.urls),

    # ИЗМЕНЕНО: используем кастомный view
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/kpi/', include('apps.kpi.urls')),
]