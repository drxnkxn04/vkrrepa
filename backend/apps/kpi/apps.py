# backend/apps/kpi/apps.py

from django.apps import AppConfig


class KpiConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'apps.kpi'

    def ready(self):
        import apps.kpi.signals  # Подключаем сигналы
