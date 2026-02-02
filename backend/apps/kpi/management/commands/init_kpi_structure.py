# backend/apps/kpi/management/commands/init_kpi_structure.py

from django.core.management.base import BaseCommand
from apps.kpi.models import KpiGroup, KpiIndicator


class Command(BaseCommand):
    help = 'Инициализация структуры KPI показателей из ВКР'

    def handle(self, *args, **options):
        self.stdout.write('Создание структуры KPI...')

        # Очистка существующих данных (опционально)
        # KpiGroup.objects.all().delete()

        # 1. ГРУППА: Научная и творческая деятельность
        group_science, _ = KpiGroup.objects.get_or_create(
            name='Научная и творческая деятельность',
            defaults={
                'description': 'Публикации, патенты, конференции',
                'weight': 0.40,  # 40% от общего балла
                'order': 1
            }
        )

        # Показатели группы "Наука"
        indicators_science = [
            {
                'name': 'Статьи в журналах Scopus/WoS Q1-Q2',
                'description': 'Публикации в высокорейтинговых международных журналах',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 3.0,
                'data_source': 'api',
                'order': 1
            },
            {
                'name': 'Статьи в журналах Scopus/WoS Q3-Q4',
                'description': 'Публикации в международных журналах',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 2.0,
                'data_source': 'api',
                'order': 2
            },
            {
                'name': 'Статьи в журналах ВАК',
                'description': 'Публикации в российских журналах ВАК',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 1.5,
                'data_source': 'manual',
                'order': 3
            },
            {
                'name': 'Публикации в трудах конференций',
                'description': 'Статьи в сборниках конференций',
                'max_value': 15.0,
                'unit': 'шт.',
                'weight': 1.0,
                'data_source': 'api',
                'order': 4
            },
            {
                'name': 'Монографии',
                'description': 'Авторские и коллективные монографии',
                'max_value': 2.0,
                'unit': 'шт.',
                'weight': 3.0,
                'data_source': 'manual',
                'order': 5
            },
            {
                'name': 'Патенты и свидетельства',
                'description': 'Патенты на изобретения, свидетельства на ПО',
                'max_value': 3.0,
                'unit': 'шт.',
                'weight': 2.5,
                'data_source': 'manual',
                'order': 6
            }
        ]

        for ind_data in indicators_science:
            KpiIndicator.objects.get_or_create(
                group=group_science,
                name=ind_data['name'],
                defaults=ind_data
            )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создана группа "{group_science.name}" с {len(indicators_science)} показателями'
        ))

        # 2. ГРУППА: Образовательная деятельность
        group_education, _ = KpiGroup.objects.get_or_create(
            name='Образовательная деятельность',
            defaults={
                'description': 'Преподавание, руководство студентами, методические материалы',
                'weight': 0.30,  # 30% от общего балла
                'order': 2
            }
        )

        indicators_education = [
            {
                'name': 'Учебная нагрузка',
                'description': 'Объем аудиторной нагрузки (часы)',
                'max_value': 800.0,
                'unit': 'ч.',
                'weight': 1.0,
                'data_source': 'manual',
                'order': 1
            },
            {
                'name': 'Учебные пособия',
                'description': 'Изданные учебники и учебные пособия',
                'max_value': 3.0,
                'unit': 'шт.',
                'weight': 2.0,
                'data_source': 'manual',
                'order': 2
            },
            {
                'name': 'Руководство ВКР',
                'description': 'Количество защищенных выпускных работ',
                'max_value': 10.0,
                'unit': 'чел.',
                'weight': 1.5,
                'data_source': 'manual',
                'order': 3
            },
            {
                'name': 'Руководство аспирантами',
                'description': 'Научное руководство аспирантами',
                'max_value': 5.0,
                'unit': 'чел.',
                'weight': 2.5,
                'data_source': 'manual',
                'order': 4
            }
        ]

        for ind_data in indicators_education:
            KpiIndicator.objects.get_or_create(
                group=group_education,
                name=ind_data['name'],
                defaults=ind_data
            )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создана группа "{group_education.name}" с {len(indicators_education)} показателями'
        ))

        # 3. ГРУППА: Финансовые показатели
        group_finance, _ = KpiGroup.objects.get_or_create(
            name='Финансовые показатели',
            defaults={
                'description': 'Гранты, договоры, привлечение средств',
                'weight': 0.15,  # 15% от общего балла
                'order': 3
            }
        )

        indicators_finance = [
            {
                'name': 'Гранты РНФ',
                'description': 'Федеральные научные гранты',
                'max_value': 2.0,
                'unit': 'шт.',
                'weight': 3.0,
                'data_source': 'manual',
                'order': 1
            },
            {
                'name': 'Хоздоговоры',
                'description': 'Договоры с предприятиями и организациями',
                'max_value': 3.0,
                'unit': 'шт.',
                'weight': 2.0,
                'data_source': 'manual',
                'order': 2
            },
            {
                'name': 'Внебюджетные средства',
                'description': 'Привлеченные внебюджетные средства',
                'max_value': 1000000.0,
                'unit': '₽',
                'weight': 1.5,
                'data_source': 'manual',
                'order': 3
            }
        ]

        for ind_data in indicators_finance:
            KpiIndicator.objects.get_or_create(
                group=group_finance,
                name=ind_data['name'],
                defaults=ind_data
            )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создана группа "{group_finance.name}" с {len(indicators_finance)} показателями'
        ))

        # 4. ГРУППА: Административная деятельность
        group_admin, _ = KpiGroup.objects.get_or_create(
            name='Административная деятельность',
            defaults={
                'description': 'Участие в комиссиях, советах, редколлегиях',
                'weight': 0.10,  # 10% от общего балла
                'order': 4
            }
        )

        indicators_admin = [
            {
                'name': 'Работа в приемной комиссии',
                'description': 'Участие в приемной кампании',
                'max_value': 1.0,
                'unit': 'да/нет',
                'weight': 1.0,
                'data_source': 'manual',
                'order': 1
            },
            {
                'name': 'Участие в ученых советах',
                'description': 'Членство в советах вуза/факультета',
                'max_value': 2.0,
                'unit': 'шт.',
                'weight': 1.5,
                'data_source': 'manual',
                'order': 2
            },
            {
                'name': 'Редколлегии журналов',
                'description': 'Членство в редакционных коллегиях',
                'max_value': 3.0,
                'unit': 'шт.',
                'weight': 2.0,
                'data_source': 'manual',
                'order': 3
            }
        ]

        for ind_data in indicators_admin:
            KpiIndicator.objects.get_or_create(
                group=group_admin,
                name=ind_data['name'],
                defaults=ind_data
            )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создана группа "{group_admin.name}" с {len(indicators_admin)} показателями'
        ))

        # 5. ГРУППА: Международная деятельность
        group_international, _ = KpiGroup.objects.get_or_create(
            name='Международная деятельность',
            defaults={
                'description': 'Международные проекты, стажировки, гранты',
                'weight': 0.05,  # 5% от общего балла
                'order': 5
            }
        )

        indicators_international = [
            {
                'name': 'Международные гранты',
                'description': 'Участие в международных грантах',
                'max_value': 2.0,
                'unit': 'шт.',
                'weight': 3.0,
                'data_source': 'manual',
                'order': 1
            },
            {
                'name': 'Зарубежные стажировки',
                'description': 'Стажировки в зарубежных университетах',
                'max_value': 1.0,
                'unit': 'шт.',
                'weight': 2.5,
                'data_source': 'manual',
                'order': 2
            },
            {
                'name': 'Международные проекты',
                'description': 'Участие в международных научных проектах',
                'max_value': 3.0,
                'unit': 'шт.',
                'weight': 2.0,
                'data_source': 'manual',
                'order': 3
            }
        ]

        for ind_data in indicators_international:
            KpiIndicator.objects.get_or_create(
                group=group_international,
                name=ind_data['name'],
                defaults=ind_data
            )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создана группа "{group_international.name}" с {len(indicators_international)} показателями'
        ))

        # Итоговая статистика
        total_groups = KpiGroup.objects.count()
        total_indicators = KpiIndicator.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Инициализация завершена!'
        ))
        self.stdout.write(f'   Всего групп: {total_groups}')
        self.stdout.write(f'   Всего показателей: {total_indicators}')
        self.stdout.write(f'\n Теперь можно создавать KpiValue для пользователей')