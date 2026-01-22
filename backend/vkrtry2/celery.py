from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vktry2.settings')

# Создание экземпляра приложения Celery
app = Celery('vktry2')

# Загрузка настроек из settings.py с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическая загрузка задач из всех зарегистрированных приложений Django
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    'collect-publications-daily': {
        'task': 'apps.integrations.services.crossref_service.collect_publications',
        'schedule': crontab(minute=0, hour=2),  # Запуск в 2:00 каждый день
    },
    'generate-monthly-reports': {
        'task': 'apps.kpi.tasks.generate_monthly_reports',
        'schedule': crontab(0, 0, day_of_month='1'),  # Запуск в 00:00 1-го числа каждого месяца
    },
    'send-kpi-reminders': {
        'task': 'apps.kpi.tasks.send_kpi_reminders',
        'schedule': crontab(minute=0, hour=9),  # Запуск в 9:00 каждый день
    }
}

# Опционально: настройка для работы с Redis
app.conf.broker_connection_retry_on_startup = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')