# backend/apps/kpi/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import datetime
import logging

from .services import KpiCalculator, CrossrefKpiIntegration
# ↑ Импорт через services/__init__.py

logger = logging.getLogger(__name__)


@shared_task
def calculate_kpi_for_all_users(period=None):
    """
    Периодическая задача: расчет KPI для всех пользователей.
    Запускается автоматически в конце месяца.

    Args:
        period: Период в формате 'YYYY-MM' (если None, используется текущий месяц)
    """
    calculator = KpiCalculator()

    if period is None:
        period = timezone.now().strftime('%Y-%m')

    logger.info(f"Запуск автоматического расчета KPI за период {period}")

    try:
        result = calculator.calculate_all_users_kpi(period)
        logger.info(f"Расчет KPI завершен успешно: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при расчете KPI: {str(e)}")
        raise


@shared_task
def generate_recommendations_for_all_users(period=None):
    """
    Генерация рекомендаций для всех пользователей с низкими показателями.

    Args:
        period: Период в формате 'YYYY-MM'
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    calculator = KpiCalculator()

    if period is None:
        period = timezone.now().strftime('%Y-%m')

    logger.info(f"Генерация рекомендаций за период {period}")

    users = User.objects.filter(is_active=True, is_superuser=False)

    total_recommendations = 0

    for user in users:
        try:
            recommendations = calculator.generate_recommendations(user.id, period)
            total_recommendations += len(recommendations)
            logger.debug(f"Пользователь {user.username}: создано {len(recommendations)} рекомендаций")
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендаций для {user.username}: {str(e)}")

    logger.info(f"Всего создано рекомендаций: {total_recommendations}")

    return {
        'period': period,
        'users_processed': users.count(),
        'total_recommendations': total_recommendations
    }


@shared_task
def sync_crossref_publications(year=None):
    """
    Синхронизация публикаций из Crossref для всех пользователей с ORCID.

    Args:
        year: Год для синхронизации (если None, используется текущий год)
    """
    integrator = CrossrefKpiIntegration()

    if year is None:
        year = datetime.now().year

    logger.info(f"Запуск синхронизации публикаций из Crossref за {year} год")

    try:
        result = integrator.sync_all_users_publications(year)
        logger.info(f"Синхронизация завершена: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка синхронизации Crossref: {str(e)}")
        raise


@shared_task
def generate_monthly_reports(period=None):
    """
    Генерация ежемесячных отчетов по KPI.
    Запускается в первый день месяца для формирования отчетов за предыдущий месяц.

    Args:
        period: Период в формате 'YYYY-MM'
    """
    from django.contrib.auth import get_user_model
    from .report_generator import KpiReportGenerator  # Будет создан отдельно

    User = get_user_model()

    if period is None:
        # Берем предыдущий месяц
        now = timezone.now()
        if now.month == 1:
            period = f"{now.year - 1}-12"
        else:
            period = f"{now.year}-{now.month - 1:02d}"

    logger.info(f"Генерация ежемесячных отчетов за период {period}")

    users = User.objects.filter(is_active=True, is_superuser=False)
    report_generator = KpiReportGenerator()

    reports_generated = 0

    for user in users:
        try:
            report_path = report_generator.generate_user_report(user.id, period)
            logger.debug(f"Отчет для {user.username} сохранен: {report_path}")
            reports_generated += 1
        except Exception as e:
            logger.error(f"Ошибка генерации отчета для {user.username}: {str(e)}")

    logger.info(f"Всего сгенерировано отчетов: {reports_generated}")

    return {
        'period': period,
        'reports_generated': reports_generated
    }


@shared_task
def send_kpi_notifications():
    """
    Отправка уведомлений пользователям о состоянии их KPI.
    Уведомления отправляются:
    - При низких показателях (< 70%)
    - При новых рекомендациях
    - При достижении целевых значений
    """
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.conf import settings

    User = get_user_model()
    calculator = KpiCalculator()

    period = timezone.now().strftime('%Y-%m')

    logger.info("Отправка уведомлений о KPI")

    users = User.objects.filter(is_active=True, is_superuser=False)

    notifications_sent = 0

    for user in users:
        try:
            result = calculator.calculate_total_score(user.id, period)

            # Отправляем уведомление если балл < 70%
            if result['total_score'] < 70:
                subject = "Низкий уровень KPI - требуется внимание"
                message = f"""
Здравствуйте, {user.get_full_name() or user.username}!

Ваш текущий балл KPI за {period}: {result['total_score']:.1f}%
Уровень эффективности: {result['performance_level']}

Для улучшения показателей рекомендуем ознакомиться с персональными рекомендациями в системе.

С уважением,
Система управления KPI
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True
                )

                notifications_sent += 1
                logger.debug(f"Уведомление отправлено: {user.email}")

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления для {user.username}: {str(e)}")

    logger.info(f"Отправлено уведомлений: {notifications_sent}")

    return {
        'period': period,
        'notifications_sent': notifications_sent
    }


@shared_task
def cleanup_old_recommendations():
    """
    Очистка старых выполненных рекомендаций (старше 6 месяцев).
    """
    from .models import KpiRecommendation
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=180)

    deleted_count = KpiRecommendation.objects.filter(
        is_completed=True,
        created_at__lt=cutoff_date
    ).delete()[0]

    logger.info(f"Удалено старых рекомендаций: {deleted_count}")

    return {'deleted_count': deleted_count}


# Настройка периодических задач (добавить в celery.py или settings.py)
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Расчет KPI в последний день месяца в 23:00
    'calculate-monthly-kpi': {
        'task': 'apps.kpi.tasks.calculate_kpi_for_all_users',
        'schedule': crontab(day_of_month='28-31', hour=23, minute=0),
    },

    # Генерация рекомендаций в последний день месяца в 23:30
    'generate-recommendations': {
        'task': 'apps.kpi.tasks.generate_recommendations_for_all_users',
        'schedule': crontab(day_of_month='28-31', hour=23, minute=30),
    },

    # Синхронизация публикаций каждую неделю в воскресенье в 02:00
    'sync-crossref': {
        'task': 'apps.kpi.tasks.sync_crossref_publications',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },

    # Генерация отчетов первого числа месяца в 08:00
    'generate-monthly-reports': {
        'task': 'apps.kpi.tasks.generate_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=8, minute=0),
    },

    # Отправка уведомлений каждый понедельник в 09:00
    'send-notifications': {
        'task': 'apps.kpi.tasks.send_kpi_notifications',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),
    },

    # Очистка старых данных каждый месяц
    'cleanup-old-data': {
        'task': 'apps.kpi.tasks.cleanup_old_recommendations',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),
    },
}
"""