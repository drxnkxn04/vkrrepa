# backend/apps/kpi/api/views.py

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import logging

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation, Notification
from ..serializers import (
    KpiGroupSerializer,
    KpiIndicatorSerializer,
    KpiValueSerializer,
    KpiRecommendationSerializer,
    NotificationSerializer,
)


def _create_notification(recipient, notification_type, title, message, kpi_value=None):
    Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        kpi_value=kpi_value,
    )
from ..services import KpiCalculator, KpiReportGenerator


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
        """Return KPI values with access scope."""
        qs = KpiValue.objects.select_related(
            'indicator', 'indicator__group', 'user', 'reviewer'
        )

        status_param = self.request.query_params.get('status')
        scope = self.request.query_params.get('scope')
        user_id = self.request.query_params.get('user_id')
        period = self.request.query_params.get('period')

        if self.request.user.is_staff and (scope == 'all' or status_param or user_id or self.action in ('approve', 'reject', 'pending')):
            if user_id:
                qs = qs.filter(user_id=user_id)
        else:
            qs = qs.filter(user=self.request.user)

        if status_param:
            qs = qs.filter(status=status_param)

        if period:
            qs = qs.filter(period=period)

        return qs

    def perform_create(self, serializer):
        """Auto-attach user and set draft status."""
        serializer.save(
            user=self.request.user,
            status=KpiValue.STATUS_DRAFT,
            is_verified=False
        )

    def _ensure_owner(self, obj):
        if obj.user_id != self.request.user.id:
            raise PermissionDenied('Access denied.')

    def _ensure_editable(self, obj):
        if obj.status not in (KpiValue.STATUS_DRAFT, KpiValue.STATUS_REJECTED):
            raise ValidationError('Only draft or rejected values can be edited.')

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        self._ensure_owner(obj)
        self._ensure_editable(obj)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        self._ensure_owner(obj)
        self._ensure_editable(obj)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        self._ensure_owner(obj)
        self._ensure_editable(obj)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit KPI value for review."""
        obj = self.get_object()
        self._ensure_owner(obj)

        if obj.status not in (KpiValue.STATUS_DRAFT, KpiValue.STATUS_REJECTED):
            raise ValidationError('Only draft or rejected values can be submitted.')

        obj.status = KpiValue.STATUS_SUBMITTED
        obj.submitted_at = timezone.now()
        obj.reviewer = None
        obj.reviewed_at = None
        obj.review_comment = ''
        obj.is_verified = False
        obj.save(update_fields=[
            'status', 'submitted_at', 'reviewer', 'reviewed_at', 'review_comment', 'is_verified'
        ])

        submitter_name = obj.user.get_full_name() or obj.user.username
        for staff_user in User.objects.filter(is_staff=True, is_active=True):
            _create_notification(
                recipient=staff_user,
                notification_type=Notification.TYPE_SUBMITTED,
                title='Новый KPI на проверку',
                message=f'{submitter_name} подал(а) KPI "{obj.indicator.name}" за {obj.period} на проверку.',
                kpi_value=obj,
            )

        return Response(KpiValueSerializer(obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve submitted KPI value."""
        obj = self.get_object()

        if obj.status != KpiValue.STATUS_SUBMITTED:
            raise ValidationError('Only submitted values can be approved.')

        obj.status = KpiValue.STATUS_APPROVED
        obj.is_verified = True
        obj.reviewer = request.user
        obj.reviewed_at = timezone.now()
        comment = request.data.get('review_comment')
        if comment is not None:
            obj.review_comment = comment
        obj.save(update_fields=[
            'status', 'is_verified', 'reviewer', 'reviewed_at', 'review_comment'
        ])

        reviewer_name = request.user.get_full_name() or request.user.username
        _create_notification(
            recipient=obj.user,
            notification_type=Notification.TYPE_APPROVED,
            title='KPI одобрен',
            message=f'Ваш KPI "{obj.indicator.name}" за {obj.period} одобрен руководителем {reviewer_name}.',
            kpi_value=obj,
        )

        return Response(KpiValueSerializer(obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject submitted KPI value."""
        obj = self.get_object()

        if obj.status != KpiValue.STATUS_SUBMITTED:
            raise ValidationError('Only submitted values can be rejected.')

        obj.status = KpiValue.STATUS_REJECTED
        obj.is_verified = False
        obj.reviewer = request.user
        obj.reviewed_at = timezone.now()
        comment = request.data.get('review_comment')
        if comment is not None:
            obj.review_comment = comment
        obj.save(update_fields=[
            'status', 'is_verified', 'reviewer', 'reviewed_at', 'review_comment'
        ])

        reviewer_name = request.user.get_full_name() or request.user.username
        comment_text = f' Комментарий: {obj.review_comment}' if obj.review_comment else ''
        _create_notification(
            recipient=obj.user,
            notification_type=Notification.TYPE_REJECTED,
            title='KPI отклонён',
            message=f'Ваш KPI "{obj.indicator.name}" за {obj.period} отклонён руководителем {reviewer_name}.{comment_text}',
            kpi_value=obj,
        )

        return Response(KpiValueSerializer(obj).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """List submitted KPI values pending review."""
        qs = KpiValue.objects.filter(status=KpiValue.STATUS_SUBMITTED).select_related(
            'indicator', 'indicator__group', 'user', 'reviewer'
        )
        period = request.query_params.get('period')
        if period:
            qs = qs.filter(period=period)
        return Response(KpiValueSerializer(qs, many=True, context={'request': request}).data)

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

        ДЛЯ РУКОВОДИТЕЛЕЙ: возвращает ВСЕ периоды в системе
        ДЛЯ СОТРУДНИКОВ: возвращает только их периоды

        Returns:
        Список периодов в формате YYYY-MM
        """
        user = request.user

        if user.is_staff:
            # РУКОВОДИТЕЛЬ - все периоды в системе
            periods = KpiValue.objects.filter(
                status=KpiValue.STATUS_APPROVED  # Только одобренные
            ).values_list('period', flat=True).distinct().order_by('-period')
        else:
            # СОТРУДНИК - только свои периоды
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


class GenerateUserReportView(APIView):
    """
    Generate KPI PDF report for a selected user (admin only).

    GET /api/kpi/reports/generate/<user_id>/?period=YYYY-MM
    """
    permission_classes = [IsAdminUser]

    def get(self, request, user_id, *args, **kwargs):
        period = request.query_params.get('period')

        if not period:
            return Response(
                {'error': 'Необходимо указать параметр period'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            generator = KpiReportGenerator()
            pdf_buffer = generator.generate_report_response(target_user.id, period)

            filename = f"KPI_Report_{target_user.username}_{period}.pdf"
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.error(
                f"Ошибка генерации отчета для пользователя {target_user.username}: {str(e)}"
            )
            return Response(
                {'error': 'Не удалось сгенерировать отчет'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateExcelReportView(APIView):
    """Генерация Excel-отчета для текущего пользователя. GET /api/kpi/reports/generate-excel/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period')
        if not period:
            return Response({'error': 'Необходимо указать параметр period'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            generator = KpiReportGenerator()
            buffer = generator.generate_excel_response(request.user.id, period)
            filename = f"KPI_Report_{request.user.username}_{period}.xlsx"
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            logger.error(f"Ошибка генерации Excel для {request.user.username}: {str(e)}")
            return Response({'error': 'Не удалось сгенерировать отчет'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateUserExcelReportView(APIView):
    """Генерация Excel-отчета для выбранного сотрудника (admin). GET /api/kpi/reports/generate-excel/<user_id>/"""
    permission_classes = [IsAdminUser]

    def get(self, request, user_id, *args, **kwargs):
        period = request.query_params.get('period')
        if not period:
            return Response({'error': 'Необходимо указать параметр period'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        try:
            generator = KpiReportGenerator()
            buffer = generator.generate_excel_response(target_user.id, period)
            filename = f"KPI_Report_{target_user.username}_{period}.xlsx"
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            logger.error(f"Ошибка генерации Excel для {target_user.username}: {str(e)}")
            return Response({'error': 'Не удалось сгенерировать отчет'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для уведомлений текущего пользователя.

    Endpoints:
    - GET /api/kpi/notifications/ - список уведомлений
    - GET /api/kpi/notifications/unread_count/ - количество непрочитанных
    - POST /api/kpi/notifications/{id}/read/ - отметить как прочитанное
    - POST /api/kpi/notifications/read_all/ - отметить все как прочитанные
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'count': count})
