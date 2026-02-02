# backend/apps/kpi/management/commands/populate_test_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми KPI данными для демонстрации'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начало заполнения тестовыми данными...'))

        # Создаем тестового пользователя (если еще не существует)
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'is_active': True
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.username}'))

        # Очищаем старые данные (опционально)
        KpiValue.objects.filter(user=user).delete()

        # Создаем группы KPI (если еще не существуют)
        groups_data = [
            {'name': 'Публикации', 'description': 'Научные публикации', 'weight': 0.4, 'order': 1},
            {'name': 'Проекты и гранты', 'description': 'Участие в научных проектах', 'weight': 0.3, 'order': 2},
            {'name': 'Преподавание', 'description': 'Педагогическая деятельность', 'weight': 0.2, 'order': 3},
            {'name': 'Мероприятия', 'description': 'Участие в конференциях и семинарах', 'weight': 0.1, 'order': 4},
        ]

        groups = {}
        for group_data in groups_data:
            group, _ = KpiGroup.objects.get_or_create(
                name=group_data['name'],
                defaults=group_data
            )
            groups[group_data['name']] = group

        # Создаем показатели KPI
        indicators_data = [
            # Публикации
            {'group': 'Публикации', 'name': 'Статьи Scopus/WoS', 'max_value': 10, 'unit': 'шт.', 'weight': 3.0,
             'order': 1},
            {'group': 'Публикации', 'name': 'Статьи ВАК', 'max_value': 15, 'unit': 'шт.', 'weight': 2.0, 'order': 2},
            {'group': 'Публикации', 'name': 'Статьи в трудах конференций', 'max_value': 20, 'unit': 'шт.',
             'weight': 1.0, 'order': 3},

            # Проекты
            {'group': 'Проекты и гранты', 'name': 'Гранты РНФ/РФФИ', 'max_value': 3, 'unit': 'шт.', 'weight': 2.5,
             'order': 1},
            {'group': 'Проекты и гранты', 'name': 'Хоздоговорные НИР', 'max_value': 5, 'unit': 'шт.', 'weight': 1.5,
             'order': 2},

            # Преподавание
            {'group': 'Преподавание', 'name': 'Руководство студентами', 'max_value': 30, 'unit': 'чел.', 'weight': 1.0,
             'order': 1},
            {'group': 'Преподавание', 'name': 'Методические пособия', 'max_value': 5, 'unit': 'шт.', 'weight': 1.5,
             'order': 2},

            # Мероприятия
            {'group': 'Мероприятия', 'name': 'Доклады на конференциях', 'max_value': 10, 'unit': 'шт.', 'weight': 1.0,
             'order': 1},
            {'group': 'Мероприятия', 'name': 'Организация мероприятий', 'max_value': 5, 'unit': 'шт.', 'weight': 1.5,
             'order': 2},
        ]

        indicators = {}
        for ind_data in indicators_data:
            group = groups[ind_data.pop('group')]
            indicator, _ = KpiIndicator.objects.get_or_create(
                group=group,
                name=ind_data['name'],
                defaults={**ind_data, 'data_source': 'manual'}
            )
            indicators[ind_data['name']] = indicator

        # Генерируем данные за последние 6 месяцев
        now = datetime.now()

        for month_offset in range(6):
            # Вычисляем период
            target_date = now - timedelta(days=30 * month_offset)
            period = target_date.strftime('%Y-%m')

            self.stdout.write(f'Создание данных для периода {period}...')

            # Генерируем значения для каждого показателя
            # Добавляем некоторую вариативность и тренд роста
            trend_factor = 1.0 + (month_offset * 0.05)  # Небольшой рост со временем

            values_data = [
                # Публикации (более высокие значения в начале)
                {'indicator': 'Статьи Scopus/WoS', 'actual': random.randint(3, 7) * trend_factor, 'target': 10},
                {'indicator': 'Статьи ВАК', 'actual': random.randint(5, 12) * trend_factor, 'target': 15},
                {'indicator': 'Статьи в трудах конференций', 'actual': random.randint(8, 15) * trend_factor,
                 'target': 20},

                # Проекты
                {'indicator': 'Гранты РНФ/РФФИ', 'actual': random.randint(1, 2), 'target': 3},
                {'indicator': 'Хоздоговорные НИР', 'actual': random.randint(2, 4) * trend_factor, 'target': 5},

                # Преподавание
                {'indicator': 'Руководство студентами', 'actual': random.randint(15, 25), 'target': 30},
                {'indicator': 'Методические пособия', 'actual': random.randint(1, 4), 'target': 5},

                # Мероприятия
                {'indicator': 'Доклады на конференциях', 'actual': random.randint(3, 8) * trend_factor, 'target': 10},
                {'indicator': 'Организация мероприятий', 'actual': random.randint(1, 3), 'target': 5},
            ]

            for val_data in values_data:
                indicator = indicators[val_data['indicator']]
                actual = min(val_data['actual'], val_data['target'])  # Не превышаем целевое

                KpiValue.objects.update_or_create(
                    user=user,
                    indicator=indicator,
                    period=period,
                    defaults={
                        'actual_value': round(actual, 1),
                        'target_value': val_data['target'],
                        'is_verified': True,
                        'comment': f'Тестовые данные для демонстрации за {period}'
                    }
                )

        self.stdout.write(self.style.SUCCESS('✓ Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS(f'✓ Пользователь: {user.username} / Пароль: test123'))
        self.stdout.write(self.style.SUCCESS(f'✓ Создано данных за 6 месяцев'))
        self.stdout.write(self.style.SUCCESS('Теперь можно войти в систему и увидеть графики!'))