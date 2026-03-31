# backend/apps/kpi/api/views.py

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import datetime
import logging
import re

_PERIOD_RE = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')


def _validate_period(period: str):
    """Возвращает Response(400) если period не соответствует YYYY-MM, иначе None."""
    if not _PERIOD_RE.match(period):
        return Response(
            {'error': 'Некорректный формат периода. Ожидается YYYY-MM (например, 2025-03)'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiValueLog, KpiRecommendation, Notification, KpiTarget, get_user_kpi_role
from ..serializers import (
    KpiGroupSerializer,
    KpiIndicatorSerializer,
    KpiValueSerializer,
    KpiValueLogSerializer,
    KpiRecommendationSerializer,
    KpiTargetSerializer,
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
from ..permissions import IsOwnerOrAdmin
from ..services import KpiCalculator, KpiReportGenerator


User = get_user_model()
logger = logging.getLogger(__name__)


def _log_kpi_action(kpi_value, action, actor, comment='', old_value=None, new_value=None):
    """Записывает событие в аудит-лог KPI."""
    KpiValueLog.objects.create(
        kpi_value=kpi_value,
        action=action,
        actor=actor,
        comment=comment,
        old_value=old_value,
        new_value=new_value,
    )


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
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return KPI values with access scope."""
        qs = KpiValue.objects.select_related(
            'indicator', 'indicator__group', 'user', 'reviewer'
        )

        status_param = self.request.query_params.get('status')
        scope = self.request.query_params.get('scope')
        user_id = self.request.query_params.get('user_id')
        period = self.request.query_params.get('period')

        if self.request.user.is_staff and (scope == 'all' or status_param or user_id or self.action in ('approve', 'reject', 'pending', 'logs')):
            if user_id:
                qs = qs.filter(user_id=user_id)
        else:
            qs = qs.filter(user=self.request.user)

        if status_param:
            qs = qs.filter(status=status_param)

        if period:
            qs = qs.filter(period=period)

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        """Auto-attach user and set draft status."""
        try:
            instance = serializer.save(
                user=self.request.user,
                status=KpiValue.STATUS_DRAFT,
                is_verified=False
            )
        except IntegrityError:
            raise ValidationError(
                'Значение KPI для данного показателя и периода уже существует. '
                'Вы можете отредактировать существующую запись.'
            )
        _log_kpi_action(
            instance, KpiValueLog.ACTION_CREATED, self.request.user,
            new_value=instance.actual_value,
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
        old_val = obj.actual_value
        response = super().update(request, *args, **kwargs)
        obj.refresh_from_db()
        _log_kpi_action(
            obj, KpiValueLog.ACTION_UPDATED, request.user,
            old_value=old_val, new_value=obj.actual_value,
        )
        return response

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        self._ensure_owner(obj)
        self._ensure_editable(obj)
        old_val = obj.actual_value
        response = super().partial_update(request, *args, **kwargs)
        obj.refresh_from_db()
        _log_kpi_action(
            obj, KpiValueLog.ACTION_UPDATED, request.user,
            old_value=old_val, new_value=obj.actual_value,
        )
        return response

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
        _log_kpi_action(obj, KpiValueLog.ACTION_SUBMITTED, request.user)

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
        _log_kpi_action(
            obj, KpiValueLog.ACTION_APPROVED, request.user,
            comment=obj.review_comment,
        )

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
        _log_kpi_action(
            obj, KpiValueLog.ACTION_REJECTED, request.user,
            comment=obj.review_comment,
        )

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

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Получить историю изменений для конкретного KPI-значения."""
        obj = self.get_object()
        # Владелец видит свои логи, админ — любые
        if obj.user_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Доступ запрещён.')
        logs = obj.logs.select_related('actor').all()
        return Response(KpiValueLogSerializer(logs, many=True).data)

    def _bulk_update_status(self, request, new_status, is_verified, action_type, notif_type, notif_title):
        """Общая логика массового обновления статуса KPI значений."""
        ids = request.data.get('ids', [])
        comment = request.data.get('review_comment', '')
        if not ids:
            raise ValidationError('Необходимо указать список id.')
        qs = KpiValue.objects.filter(
            id__in=ids, status=KpiValue.STATUS_SUBMITTED
        ).select_related('indicator', 'user')
        now = timezone.now()
        reviewer_name = request.user.get_full_name() or request.user.username
        count = 0
        with transaction.atomic():
            for obj in qs:
                obj.status = new_status
                obj.is_verified = is_verified
                obj.reviewer = request.user
                obj.reviewed_at = now
                if comment:
                    obj.review_comment = comment
                obj.save(update_fields=['status', 'is_verified', 'reviewer', 'reviewed_at', 'review_comment'])
                _log_kpi_action(obj, action_type, request.user, comment=comment)
                comment_text = f' Комментарий: {obj.review_comment}' if obj.review_comment and new_status == KpiValue.STATUS_REJECTED else ''
                _create_notification(
                    recipient=obj.user,
                    notification_type=notif_type,
                    title=notif_title,
                    message=f'Ваш KPI "{obj.indicator.name}" за {obj.period} {notif_title.lower().split("kpi ")[1]} руководителем {reviewer_name}.{comment_text}',
                    kpi_value=obj,
                )
                count += 1
        return count

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_approve(self, request):
        """Массовое подтверждение KPI значений."""
        count = self._bulk_update_status(
            request, KpiValue.STATUS_APPROVED, True,
            KpiValueLog.ACTION_APPROVED, Notification.TYPE_APPROVED, 'KPI одобрен',
        )
        return Response({'approved': count})

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_reject(self, request):
        """Массовое отклонение KPI значений."""
        count = self._bulk_update_status(
            request, KpiValue.STATUS_REJECTED, False,
            KpiValueLog.ACTION_REJECTED, Notification.TYPE_REJECTED, 'KPI отклонён',
        )
        return Response({'rejected': count})

    @action(detail=False, methods=['get'], pagination_class=None)
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

        err = _validate_period(period)
        if err:
            return err

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

    @action(detail=False, methods=['get'], pagination_class=None)
    def history(self, request):
        """
        Получение истории KPI за последние N месяцев.

        Query params:
        - months: количество месяцев (по умолчанию 6)

        Returns:
        Список с данными KPI по месяцам
        """
        user = request.user
        months = min(int(request.query_params.get('months', 6)), 60)

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

    @action(detail=False, methods=['get'], pagination_class=None)
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

        err = _validate_period(period)
        if err:
            return err

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

    @action(detail=False, methods=['get'], pagination_class=None)
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
            # РУКОВОДИТЕЛЬ — все периоды в системе (любой статус)
            periods = KpiValue.objects.values_list(
                'period', flat=True
            ).distinct().order_by('-period')
        else:
            # СОТРУДНИК — только свои периоды
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
    pagination_class = None

    def get_queryset(self):
        qs = KpiIndicator.objects.filter(
            data_source='manual'
        ).select_related('group')

        user_role = get_user_kpi_role(self.request.user)
        qs = qs.filter(group__role=user_role)
        return qs.order_by('group__order', 'order')


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
        role_filter = request.query_params.get('role', 'pps')  # pps | rop | all

        err = _validate_period(period)
        if err:
            return err

        try:
            calculator = KpiCalculator()
            users = User.objects.filter(
                is_active=True, is_superuser=False
            ).select_related('profile')

            if role_filter == 'pps':
                users = users.filter(is_staff=False)
            elif role_filter == 'rop':
                users = users.filter(is_staff=True)

            manager_data = []

            for user in users:
                user_kpi = calculator.calculate_total_score(user.id, period)

                manager_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                    'email': user.email,
                    'total_score': user_kpi['total_score'],
                    'total_points': user_kpi.get('total_points', 0),
                    'max_points': user_kpi.get('max_points', 0),
                    'performance_level': user_kpi['performance_level'],
                    'bonus_amount': user_kpi['bonus_amount'],
                    'user_role': user_kpi.get('user_role', 'pps'),
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
    ViewSet для работы с рекомендациями.

    Endpoints:
    - GET /api/kpi/recommendations-list/ - список рекомендаций (фильтр: ?status=active|completed|all, ?period=YYYY-MM)
    - GET /api/kpi/recommendations-list/{id}/ - конкретная рекомендация
    - POST /api/kpi/recommendations-list/{id}/complete/ - отметить как выполненную
    - POST /api/kpi/recommendations-list/{id}/uncomplete/ - вернуть в активные
    """
    serializer_class = KpiRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = KpiRecommendation.objects.filter(
            user=self.request.user,
        ).select_related('indicator', 'indicator__group')

        # Фильтр по статусу
        status_filter = self.request.query_params.get('status', 'all')
        if status_filter == 'active':
            qs = qs.filter(is_completed=False)
        elif status_filter == 'completed':
            qs = qs.filter(is_completed=True)

        # Фильтр по периоду
        period = self.request.query_params.get('period')
        if period:
            qs = qs.filter(period=period)

        return qs.order_by('is_completed', 'priority', 'current_completion')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Отметить рекомендацию как выполненную."""
        recommendation = self.get_object()
        recommendation.is_completed = True
        recommendation.save(update_fields=['is_completed', 'updated_at'])
        return Response({
            'message': 'Рекомендация отмечена как выполненная',
            'id': recommendation.id,
        })

    @action(detail=True, methods=['post'])
    def uncomplete(self, request, pk=None):
        """Вернуть рекомендацию в активные."""
        recommendation = self.get_object()
        recommendation.is_completed = False
        recommendation.save(update_fields=['is_completed', 'updated_at'])
        return Response({
            'message': 'Рекомендация возвращена в активные',
            'id': recommendation.id,
        })


class KpiGroupListView(generics.ListAPIView):
    """
    Список групп KPI с показателями (фильтр по роли пользователя).

    GET /api/kpi/groups/
    """
    serializer_class = KpiGroupSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user_role = get_user_kpi_role(self.request.user)
        return KpiGroup.objects.filter(
            role=user_role
        ).prefetch_related('indicators').order_by('order')


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
        limit = min(int(request.query_params.get('limit', 10)), 100)

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


class TeamAverageView(APIView):
    """
    Средний балл KPI по команде за период.

    GET /api/kpi/team-average/?period=YYYY-MM
    Доступен всем авторизованным пользователям.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', datetime.now().strftime('%Y-%m'))
        calculator = KpiCalculator()
        users = User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).select_related('profile')
        scores = []
        for user in users:
            try:
                result = calculator.calculate_total_score(user.id, period)
                scores.append(result['total_score'])
            except Exception:
                pass
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        return Response({
            'period': period,
            'average_score': avg,
            'user_count': len(scores),
        })


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
    pagination_class = None

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


class KpiTargetViewSet(viewsets.ModelViewSet):
    """
    Управление индивидуальными плановыми значениями (только для руководителей).

    GET /api/kpi/targets/ — список планов (фильтр: ?period=YYYY-MM&user_id=N)
    POST /api/kpi/targets/ — создать/обновить план
    DELETE /api/kpi/targets/{id}/ — удалить план
    """
    serializer_class = KpiTargetSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None

    def get_queryset(self):
        qs = KpiTarget.objects.select_related(
            'user', 'indicator', 'indicator__group', 'set_by'
        ).order_by('user__last_name', 'indicator__group__order', 'indicator__order')

        period = self.request.query_params.get('period')
        if period:
            qs = qs.filter(period=period)

        user_id = self.request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(set_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создание или обновление плана (upsert по user+indicator+period)."""
        user_id = request.data.get('user_id')
        indicator_id = request.data.get('indicator_id')
        period = request.data.get('period')
        target_value = request.data.get('target_value')
        comment = request.data.get('comment', '')

        if not all([user_id, indicator_id, period, target_value is not None]):
            return Response(
                {'error': 'Обязательные поля: user_id, indicator_id, period, target_value'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        err = _validate_period(period)
        if err:
            return err

        try:
            target_value = float(target_value)
        except (ValueError, TypeError):
            return Response(
                {'error': 'target_value должен быть числом'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target, created = KpiTarget.objects.update_or_create(
            user_id=user_id,
            indicator_id=indicator_id,
            period=period,
            defaults={
                'target_value': target_value,
                'set_by': request.user,
                'comment': comment,
            },
        )

        serializer = self.get_serializer(target)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'])
    def bulk_set(self, request):
        """
        Массовая установка планов.
        Body: { targets: [{ user_id, indicator_id, period, target_value, comment? }, ...] }
        """
        targets_data = request.data.get('targets', [])
        if not targets_data:
            return Response({'error': 'Список targets пуст'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        errors = []

        for item in targets_data:
            try:
                _, created = KpiTarget.objects.update_or_create(
                    user_id=item['user_id'],
                    indicator_id=item['indicator_id'],
                    period=item['period'],
                    defaults={
                        'target_value': float(item['target_value']),
                        'set_by': request.user,
                        'comment': item.get('comment', ''),
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                errors.append(str(e))

        return Response({
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
        })


class GenerateSummaryReportView(APIView):
    """
    Сводный PDF-отчёт по всем сотрудникам за период (только руководитель).

    GET /api/kpi/reports/summary/?period=YYYY-MM&role=pps|rop|all
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period')
        role_filter = request.query_params.get('role', 'pps')

        if not period:
            return Response(
                {'error': 'Необходимо указать параметр period'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        err = _validate_period(period)
        if err:
            return err

        try:
            generator = KpiReportGenerator()
            buffer = generator.generate_summary_report(period, role_filter)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="KPI_Summary_{period}.pdf"'
            return response
        except Exception as e:
            logger.error(f"Ошибка генерации сводного отчёта: {e}")
            return Response(
                {'error': 'Не удалось сгенерировать сводный отчёт'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GenerateSummaryExcelView(APIView):
    """
    Сводный Excel-отчёт по всем сотрудникам за период (только руководитель).

    GET /api/kpi/reports/summary-excel/?period=YYYY-MM&role=pps|rop|all
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period')
        role_filter = request.query_params.get('role', 'pps')

        if not period:
            return Response(
                {'error': 'Необходимо указать параметр period'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        err = _validate_period(period)
        if err:
            return err

        try:
            generator = KpiReportGenerator()
            buffer = generator.generate_summary_excel(period, role_filter)
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="KPI_Summary_{period}.xlsx"'
            return response
        except Exception as e:
            logger.error(f"Ошибка генерации сводного Excel: {e}")
            return Response(
                {'error': 'Не удалось сгенерировать сводный отчёт'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
