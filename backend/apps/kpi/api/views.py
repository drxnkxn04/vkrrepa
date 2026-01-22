# backend/apps/kpi/api/views.py

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import logging

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation
from ..serializers import (
    KpiGroupSerializer,
    KpiIndicatorSerializer,
    KpiValueSerializer,
    KpiRecommendationSerializer
)
from ..services import KpiCalculator, CrossrefKpiIntegration, KpiReportGenerator


User = get_user_model()
logger = logging.getLogger(__name__)


class KpiValueViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с значениями KPI.

    Endpoints:
    - GET /api/kpi/values/ - список значений текущего пользователя
    - POST /api/kpi/values/ - создание нового значения
    - GET /api/kpi/values/{id}/ - получение конкретного значения
    - PUT/PATCH /api/kpi/values/{id}/ - обновление значения
    - DELETE /api/kpi/values/{id}/ - удаление значения
    - GET /api/kpi/values/dashboard/ - данные для дашборда
    - GET /api/kpi/values/history/ - история KPI
    - GET /api/kpi/values/recommendations/ - рекомендации
    - GET /api/kpi/values/periods/ - доступные периоды
    """
    serializer_class = KpiValueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает только значения текущего пользователя."""
        return KpiValue.objects.filter(user=self.request.user).select_related(
            'indicator', 'indicator__group'
        )

    def perform_create(self, serializer):
        """Автоматически устанавливает текущего пользователя при создании."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Получение данных для дашборда пользователя.

        Query params:
        - period: период в формате YYYY-MM (по умолчанию текущий месяц)

        Returns:
        - total_score: итоговый балл KPI
        - performance_level: уровень эффективности
        - bonus_amount: сумма премии
        - group_scores: баллы по группам с детализацией
        """
        user = request.user
        period = request.query_params.get('period', datetime.now().strftime('%Y-%m'))

        try:
            calculator = KpiCalculator()
            dashboard_data = calculator.calculate_dashboard(user.id, period)
            return Response(dashboard_data)
        except Exception as e:
            logger.error(f"Ошибка получения данных дашборда для {user.username}: {str(e)}")
            return Response(
                {'error': 'Не удалось загрузить данные дашборда'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Получение истории KPI за последние N месяцев.

        Query params:
        - months: количество месяцев (по умолчанию 6)

        Returns:
        Список с данными KPI по месяцам
        """
        user = request.user
        months = int(request.query_params.get('months', 6))

        try:
            calculator = KpiCalculator()
            history = calculator.get_user_kpi_history(user.id, months)
            return Response(history)
        except Exception as e:
            logger.error(f"Ошибка получения истории KPI для {user.username}: {str(e)}")
            return Response(
                {'error': 'Не удалось загрузить историю KPI'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Получение персонализированных рекомендаций.

        Query params:
        - period: период в формате YYYY-MM (по умолчанию текущий месяц)

        Returns:
        Список рекомендаций для улучшения показателей
        """
        user = request.user
        period = request.query_params.get('period', datetime.now().strftime('%Y-%m'))

        try:
            calculator = KpiCalculator()
            recommendations = calculator.generate_recommendations(user.id, period)
            return Response(recommendations)
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций для {user.username}: {str(e)}")
            return Response(
                {'error': 'Не удалось загрузить рекомендации'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def periods(self, request):
        """
        Получение списка доступных периодов с данными.

        Returns:
        Список периодов в формате YYYY-MM
        """
        user = request.user

        # Получаем уникальные периоды из KpiValue для текущего пользователя
        periods = KpiValue.objects.filter(
            user=user
        ).values_list('period', flat=True).distinct().order_by('-period')

        return Response(list(periods))


class ManualKpiIndicatorListView(generics.ListAPIView):
    """
    Список показателей KPI, доступных для ручного ввода.

    GET /api/kpi/indicators/manual/

    Returns:
    Список индикаторов с data_source='manual'
    """
    serializer_class = KpiIndicatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return KpiIndicator.objects.filter(
            data_source='manual'
        ).select_related('group').order_by('group__order', 'order')


class ManagerDashboardView(APIView):
    """
    Дашборд для руководителя с данными по всем сотрудникам.

    GET /api/kpi/manager-dashboard/

    Query params:
    - period: период в формате YYYY-MM (по умолчанию текущий месяц)

    Доступен только для администраторов (is_staff=True).
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', timezone.now().strftime('%Y-%m'))

        try:
            calculator = KpiCalculator()
            users = User.objects.filter(is_active=True, is_superuser=False)

            manager_data = []

            for user in users:
                user_kpi = calculator.calculate_total_score(user.id, period)

                manager_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                    'email': user.email,
                    'total_score': user_kpi['total_score'],
                    'performance_level': user_kpi['performance_level'],
                    'bonus_amount': user_kpi['bonus_amount']
                })

            # Сортировка по баллу (лучшие сверху)
            manager_data.sort(key=lambda x: x['total_score'], reverse=True)

            return Response({
                'period': period,
                'total_users': len(manager_data),
                'users': manager_data
            })

        except Exception as e:
            logger.error(f"Ошибка получения данных дашборда руководителя: {str(e)}")
            return Response(
                {'error': 'Не удалось загрузить данные'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateReportView(APIView):
    """
    Генерация PDF-отчета по KPI.

    GET /api/kpi/reports/generate/

    Query params:
    - period: период в формате YYYY-MM (обязательный)

    Returns:
    PDF файл с отчетом
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period')

        if not period:
            return Response(
                {'error': 'Необходимо указать параметр period'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            generator = KpiReportGenerator()
            pdf_buffer = generator.generate_report_response(request.user.id, period)

            # Формирование имени файла
            filename = f"KPI_Report_{request.user.username}_{period}.pdf"

            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            logger.error(f"Ошибка генерации отчета для {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Не удалось сгенерировать отчет'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossrefSyncView(APIView):
    """
    Синхронизация публикаций из Crossref API.

    POST /api/kpi/crossref/sync/

    Body:
    - orcid: ORCID идентификатор (необязательно, берется из профиля)
    - year: год для синхронизации (необязательно, по умолчанию текущий)

    Returns:
    Статистика синхронизации
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        orcid = request.data.get('orcid')
        year = request.data.get('year')

        # Если ORCID не передан, пытаемся взять из профиля
        if not orcid:
            if hasattr(user, 'profile') and user.profile.orcid:
                orcid = user.profile.orcid
            else:
                return Response(
                    {'error': 'ORCID не указан в профиле пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            integrator = CrossrefKpiIntegration()
            result = integrator.sync_user_publications(user.id, orcid, year)

            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Ошибка синхронизации Crossref для {user.username}: {str(e)}")
            return Response(
                {'error': 'Не удалось выполнить синхронизацию'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с рекомендациями (только чтение).

    Endpoints:
    - GET /api/kpi/recommendations-list/ - список рекомендаций
    - GET /api/kpi/recommendations-list/{id}/ - конкретная рекомендация
    - POST /api/kpi/recommendations-list/{id}/complete/ - отметить как выполненную
    """
    serializer_class = KpiRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return KpiRecommendation.objects.filter(
            user=self.request.user,
            is_completed=False
        ).select_related('indicator', 'indicator__group').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Отметить рекомендацию как выполненную.

        POST /api/kpi/recommendations-list/{id}/complete/
        """
        try:
            recommendation = self.get_object()
            recommendation.is_completed = True
            recommendation.save()

            return Response({
                'message': 'Рекомендация отмечена как выполненная',
                'id': recommendation.id
            })
        except Exception as e:
            logger.error(f"Ошибка отметки рекомендации: {str(e)}")
            return Response(
                {'error': 'Не удалось обновить рекомендацию'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KpiGroupListView(generics.ListAPIView):
    """
    Список всех групп KPI с показателями.

    GET /api/kpi/groups/
    """
    serializer_class = KpiGroupSerializer
    permission_classes = [IsAuthenticated]
    queryset = KpiGroup.objects.all().prefetch_related('indicators').order_by('order')


class TopPerformersView(APIView):
    """
    Список лучших сотрудников за период.

    GET /api/kpi/top-performers/

    Query params:
    - period: период в формате YYYY-MM (по умолчанию текущий месяц)
    - limit: количество сотрудников (по умолчанию 10)

    Доступен только для администраторов.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', datetime.now().strftime('%Y-%m'))
        limit = int(request.query_params.get('limit', 10))

        try:
            calculator = KpiCalculator()
            top_performers = calculator.get_top_performers(period, limit)

            return Response({
                'period': period,
                'top_performers': top_performers
            })

        except Exception as e:
            logger.error(f"Ошибка получения топа сотрудников: {str(e)}")
            return Response(
                {'error': 'Не удалось загрузить данные'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )