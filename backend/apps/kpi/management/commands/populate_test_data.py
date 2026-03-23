# backend/apps/kpi/management/commands/populate_test_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue, UserProfile
from datetime import datetime
import random

User = get_user_model()


# Тестовые сотрудники ППС
PPS_EMPLOYEES = [
    {'username': 'ivanov', 'first_name': 'Иван', 'last_name': 'Иванов', 'email': 'ivanov@ai-center.ru',
     'department': 'Лаборатория машинного обучения', 'position': 'Доцент'},
    {'username': 'petrova', 'first_name': 'Анна', 'last_name': 'Петрова', 'email': 'petrova@ai-center.ru',
     'department': 'Лаборатория компьютерного зрения', 'position': 'Старший преподаватель'},
    {'username': 'sidorov', 'first_name': 'Дмитрий', 'last_name': 'Сидоров', 'email': 'sidorov@ai-center.ru',
     'department': 'Лаборатория NLP', 'position': 'Профессор'},
    {'username': 'kuznetsova', 'first_name': 'Мария', 'last_name': 'Кузнецова', 'email': 'kuznetsova@ai-center.ru',
     'department': 'Лаборатория робототехники', 'position': 'Доцент'},
    {'username': 'volkov', 'first_name': 'Алексей', 'last_name': 'Волков', 'email': 'volkov@ai-center.ru',
     'department': 'Лаборатория анализа данных', 'position': 'Ассистент'},
]

# Руководитель РОП
ROP_EMPLOYEE = {
    'username': 'smirnov', 'first_name': 'Сергей', 'last_name': 'Смирнов', 'email': 'smirnov@ai-center.ru',
    'department': 'Центр ИИ', 'position': 'Руководитель центра',
}

# Профили производительности для разнообразия
PERFORMANCE_PROFILES = {
    'high': (0.85, 1.0),       # 85-100% выполнения
    'medium': (0.55, 0.80),    # 55-80%
    'low': (0.20, 0.50),       # 20-50%
    'growing': None,           # Растущий тренд (обрабатывается отдельно)
}

PASSWORD = 'test1234'


class Command(BaseCommand):
    help = 'Создание тестовых сотрудников с KPI-данными за 6 месяцев'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Удалить существующих тестовых пользователей и их данные',
        )

    def handle(self, *args, **options):
        if options['clear']:
            usernames = [e['username'] for e in PPS_EMPLOYEES] + [ROP_EMPLOYEE['username']]
            deleted = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f'Удалено: {deleted}'))

        self.stdout.write('Создание тестовых сотрудников...\n')

        # Назначаем каждому сотруднику профиль производительности
        profiles = ['high', 'medium', 'medium', 'low', 'growing']

        for emp_data, perf_profile in zip(PPS_EMPLOYEES, profiles):
            user = self._create_user(emp_data, role='pps')
            self._generate_kpi_data(user, 'pps', perf_profile)
            self.stdout.write(
                f'  {user.get_full_name()} ({emp_data["position"]}) '
                f'- профиль: {perf_profile}'
            )

        # РОП
        rop_user = self._create_user(ROP_EMPLOYEE, role='rop', is_staff=False)
        self._generate_kpi_data(rop_user, 'rop', 'high')
        self.stdout.write(
            f'  {rop_user.get_full_name()} ({ROP_EMPLOYEE["position"]}) '
            f'- профиль: high (РОП)'
        )

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово! Создано 6 сотрудников. Пароль для всех: {PASSWORD}'
        ))
        self.stdout.write('Логины: ' + ', '.join(
            [e['username'] for e in PPS_EMPLOYEES] + [ROP_EMPLOYEE['username']]
        ))

    def _create_user(self, data, role='pps', is_staff=False):
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email'],
                'is_active': True,
                'is_staff': is_staff,
            }
        )
        if created:
            user.set_password(PASSWORD)
            user.save()

        # Обновляем профиль
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.department = data['department']
        profile.position = data['position']
        profile.save()

        return user

    def _generate_kpi_data(self, user, role, perf_profile):
        """Генерация KPI-данных за последние 6 месяцев."""
        KpiValue.objects.filter(user=user).delete()

        indicators = KpiIndicator.objects.filter(
            group__role=role,
        ).select_related('group')

        now = datetime.now()
        periods = []
        y, m = now.year, now.month
        for i in range(6):
            cm = m - i
            cy = y
            while cm <= 0:
                cm += 12
                cy -= 1
            periods.append(f'{cy}-{cm:02d}')
        periods.reverse()  # от старого к новому

        for idx, period in enumerate(periods):
            for indicator in indicators:
                if perf_profile == 'growing':
                    # Рост от 30% до 85% за 6 месяцев
                    base = 0.30 + (idx / 5) * 0.55
                    factor = base + random.uniform(-0.10, 0.10)
                    factor = max(0.15, min(factor, 1.0))
                else:
                    lo, hi = PERFORMANCE_PROFILES[perf_profile]
                    factor = random.uniform(lo, hi)

                actual = round(indicator.max_value * factor, 1)
                actual = min(actual, indicator.max_value)

                KpiValue.objects.create(
                    user=user,
                    indicator=indicator,
                    period=period,
                    actual_value=actual,
                    target_value=indicator.max_value,
                    is_verified=True,
                    status=KpiValue.STATUS_APPROVED,
                    comment=f'Тестовые данные ({perf_profile})',
                )
