# backend/vkrtry2/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# ⚠️ ИСПРАВЛЕНО: было vktry2, должно быть vkrtry2
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkrtry2.settings')

app = Celery('vkrtry2')  # ⚠️ И здесь тоже

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Периодические задачи
app.conf.beat_schedule = {
    'calculate-monthly-kpi': {
        'task': 'apps.kpi.tasks.calculate_kpi_for_all_users',
        'schedule': crontab(day_of_month='28-31', hour=23, minute=0),
    },
    'generate-recommendations': {
        'task': 'apps.kpi.tasks.generate_recommendations_for_all_users',
        'schedule': crontab(day_of_month='28-31', hour=23, minute=30),
    },
}

app.conf.broker_connection_retry_on_startup = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')