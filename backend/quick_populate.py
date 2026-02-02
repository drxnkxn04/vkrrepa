#!/usr/bin/env python
"""
Быстрое заполнение базы данных тестовыми KPI данными

Использование:
1. Скопируй этот файл в папку backend/
2. Запусти: python quick_populate.py
"""

import os
import django
import sys

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkrtry2.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue
from datetime import datetime, timedelta
import random

User = get_user_model()


def create_test_data():
    print(' Начало заполнения тестовыми данными...\n')

    # 1. Создаем тестового пользователя
    print(' Создание тестового пользователя...')
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
        print(f'   ✓ Создан: {user.username}')
    else:
        print(f'   ✓ Уже существует: {user.username}')

    # Очищаем старые данные
    deleted_count = KpiValue.objects.filter(user=user).delete()[0]
    if deleted_count > 0:
        print(f'   ✓ Удалено старых записей: {deleted_count}')

    # 2. Создаем группы KPI
    print('\n Создание групп показателей...')
    groups_data = [
        {'name': 'Публикации', 'description': 'Научные публикации', 'weight': 0.4, 'order': 1},
        {'name': 'Проекты и гранты', 'description': 'Участие в научных проектах', 'weight': 0.3, 'order': 2},
        {'name': 'Преподавание', 'description': 'Педагогическая деятельность', 'weight': 0.2, 'order': 3},
        {'name': 'Мероприятия', 'description': 'Участие в конференциях и семинарах', 'weight': 0.1, 'order': 4},
    ]

    groups = {}
    for group_data in groups_data:
        group, created = KpiGroup.objects.get_or_create(
            name=group_data['name'],
            defaults=group_data
        )
        groups[group_data['name']] = group
        status = '✓ Создана' if created else '✓ Существует'
        print(f'   {status}: {group.name}')

    # 3. Создаем показатели KPI
    print('\n Создание показателей KPI...')
    indicators_data = [
        # Публикации
        {'group': 'Публикации', 'name': 'Статьи Scopus/WoS', 'max_value': 10, 'unit': 'шт.', 'weight': 3.0, 'order': 1},
        {'group': 'Публикации', 'name': 'Статьи ВАК', 'max_value': 15, 'unit': 'шт.', 'weight': 2.0, 'order': 2},
        {'group': 'Публикации', 'name': 'Статьи в трудах конференций', 'max_value': 20, 'unit': 'шт.', 'weight': 1.0,
         'order': 3},

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
        indicator, created = KpiIndicator.objects.get_or_create(
            group=group,
            name=ind_data['name'],
            defaults={**ind_data, 'data_source': 'manual'}
        )
        indicators[ind_data['name']] = indicator
        status = '✓' if created else '•'
        print(f'   {status} {indicator.name}')

    # 4. Генерируем данные за последние 6 месяцев
    print('\n Генерация данных за 6 месяцев...')
    now = datetime.now()
    total_created = 0

    for month_offset in range(6):
        target_date = now - timedelta(days=30 * month_offset)
        period = target_date.strftime('%Y-%m')

        # Тренд роста
        trend_factor = 1.0 + (month_offset * 0.05)

        values_data = [
            # Публикации
            {'indicator': 'Статьи Scopus/WoS', 'actual': random.randint(3, 7) * trend_factor, 'target': 10},
            {'indicator': 'Статьи ВАК', 'actual': random.randint(5, 12) * trend_factor, 'target': 15},
            {'indicator': 'Статьи в трудах конференций', 'actual': random.randint(8, 15) * trend_factor, 'target': 20},

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

        period_count = 0
        for val_data in values_data:
            indicator = indicators[val_data['indicator']]
            actual = min(val_data['actual'], val_data['target'])

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
            period_count += 1

        total_created += period_count
        print(f'   ✓ {period}: создано {period_count} записей')

    print(f'\ ГОТОВО! Всего создано {total_created} записей KPI')
    print('\n' + '=' * 60)
    print(' Данные для демонстрации успешно загружены!')
    print('=' * 60)
    print('\n Данные для входа:')
    print(f'   Username: testuser')
    print(f'   Password: test123')
    print('\n Следующие шаги:')
    print('   1. Запусти сервер: python manage.py runserver')
    print('   2. Открой http://localhost:8000/')
    print('   3. Войди с указанными учетными данными')
    print('   4. Наслаждайся графиками и данными! ')
    print('\n')


if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f'\n❌ Ошибка: {e}')
        print('Убедись, что запускаешь скрипт из папки backend/')
        sys.exit(1)