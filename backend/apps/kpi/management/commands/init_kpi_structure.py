# backend/apps/kpi/management/commands/init_kpi_structure.py

from django.core.management.base import BaseCommand
from apps.kpi.models import KpiGroup, KpiIndicator


class Command(BaseCommand):
    help = 'Инициализация структуры KPI показателей (ППС и РОП) из реальных данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить существующие группы и показатели перед созданием',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Удаление существующих данных...'))
            KpiIndicator.objects.all().delete()
            KpiGroup.objects.all().delete()

        self.stdout.write('Создание структуры KPI...\n')

        self._create_pps_structure()
        self._create_rop_structure()

        # Итоговая статистика
        pps_groups = KpiGroup.objects.filter(role=KpiGroup.ROLE_PPS).count()
        rop_groups = KpiGroup.objects.filter(role=KpiGroup.ROLE_ROP).count()
        total_indicators = KpiIndicator.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Инициализация завершена!'
        ))
        self.stdout.write(f'   Групп ППС: {pps_groups}')
        self.stdout.write(f'   Групп РОП: {rop_groups}')
        self.stdout.write(f'   Всего показателей: {total_indicators}')

    def _create_pps_structure(self):
        """
        Структура KPI для ППС (преподаватель).
        Итого: 500 баллов, 5 групп, 8 показателей.
        Бонус: +15% при высоком, -50% при низком.
        """
        self.stdout.write('\n--- ППС (преподаватель) ---')

        # === Группа 1: Публикационная активность (100 б.) ===
        g1, _ = KpiGroup.objects.get_or_create(
            name='Публикационная активность',
            role=KpiGroup.ROLE_PPS,
            defaults={
                'description': 'Научные публикации и конференции',
                'weight': 0.20,  # 100/500
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 1,
            }
        )
        self._create_indicators(g1, [
            {
                'name': 'Публикации в рецензируемых журналах',
                'description': 'Статьи в рецензируемых научных журналах (Scopus, WoS, ВАК)',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 0.5,
                'max_points': 50.0,
                'data_source': 'api',
                'order': 1,
            },
            {
                'name': 'Материалы конференций CORE A*/A',
                'description': 'Публикации в трудах конференций уровня CORE A*/A',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 0.5,
                'max_points': 50.0,
                'data_source': 'api',
                'order': 2,
            },
        ])

        # === Группа 2: Качество образовательного процесса (100 б.) ===
        g2, _ = KpiGroup.objects.get_or_create(
            name='Качество образовательного процесса',
            role=KpiGroup.ROLE_PPS,
            defaults={
                'description': 'Преподавание, нагрузка, методические материалы',
                'weight': 0.20,  # 100/500
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 2,
            }
        )
        self._create_indicators(g2, [
            {
                'name': 'Доля практических занятий',
                'description': 'Процент практических/лабораторных занятий в общей нагрузке',
                'max_value': 100.0,
                'unit': '%',
                'weight': 0.20,
                'max_points': 20.0,
                'data_source': 'manual',
                'order': 1,
            },
            {
                'name': 'Учебная нагрузка в кредитах',
                'description': 'Объём преподавательской нагрузки в кредитах ECTS',
                'max_value': 30.0,
                'unit': 'кр.',
                'weight': 0.30,
                'max_points': 30.0,
                'data_source': 'manual',
                'order': 2,
            },
            {
                'name': 'Разработанные учебные материалы/РПД',
                'description': 'Подготовленные рабочие программы дисциплин и учебные материалы',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 0.50,
                'max_points': 50.0,
                'data_source': 'manual',
                'order': 3,
            },
        ])

        # === Группа 3: Участие в НИР (100 б.) ===
        g3, _ = KpiGroup.objects.get_or_create(
            name='Участие в НИР',
            role=KpiGroup.ROLE_PPS,
            defaults={
                'description': 'Научно-исследовательские работы и гранты',
                'weight': 0.20,  # 100/500
                'max_points': 100.0,
                'min_threshold': 100.0,
                'order': 3,
            }
        )
        self._create_indicators(g3, [
            {
                'name': 'НИОКР и гранты',
                'description': 'Участие в научно-исследовательских и опытно-конструкторских работах, грантах',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 1.0,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 1,
            },
        ])

        # === Группа 4: Практическая работа в ИИ (100 б.) ===
        g4, _ = KpiGroup.objects.get_or_create(
            name='Практическая работа в ИИ',
            role=KpiGroup.ROLE_PPS,
            defaults={
                'description': 'Внедрённые проекты в области искусственного интеллекта',
                'weight': 0.20,  # 100/500
                'max_points': 100.0,
                'min_threshold': 100.0,
                'order': 4,
            }
        )
        self._create_indicators(g4, [
            {
                'name': 'Внедрённые проекты',
                'description': 'Реализованные и внедрённые проекты в области ИИ',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 1.0,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 1,
            },
        ])

        # === Группа 5: Международные мероприятия (100 б.) ===
        g5, _ = KpiGroup.objects.get_or_create(
            name='Международные мероприятия',
            role=KpiGroup.ROLE_PPS,
            defaults={
                'description': 'Доклады и выступления на международных конференциях',
                'weight': 0.20,  # 100/500
                'max_points': 100.0,
                'min_threshold': 100.0,
                'order': 5,
            }
        )
        self._create_indicators(g5, [
            {
                'name': 'Доклады на конференциях',
                'description': 'Доклады и выступления на международных научных конференциях',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 1.0,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 1,
            },
        ])

        self.stdout.write(self.style.SUCCESS(
            '[OK] ППС: 5 групп, 8 показателей, итого 500 баллов'
        ))

    def _create_rop_structure(self):
        """
        Структура KPI для РОП (руководитель образовательной программы).
        Итого: 700 баллов, 6 групп, 14 показателей.
        Бонус: +15% при высоком, -50% при низком.
        """
        self.stdout.write('\n--- РОП (руководитель) ---')

        # === Группа 1: Реализация образовательных программ (100 б.) ===
        g1, _ = KpiGroup.objects.get_or_create(
            name='Реализация образовательных программ',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Учебная нагрузка, аттестация, вовлечение студентов',
                'weight': 100.0 / 700.0,
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 1,
            }
        )
        self._create_indicators(g1, [
            {
                'name': 'Учебная нагрузка',
                'description': 'Объём преподавательской нагрузки',
                'max_value': 800.0,
                'unit': 'ч.',
                'weight': 0.40,
                'max_points': 40.0,
                'data_source': 'manual',
                'order': 1,
            },
            {
                'name': 'Доля студентов, прошедших аттестацию',
                'description': 'Процент студентов, успешно прошедших промежуточную аттестацию',
                'max_value': 100.0,
                'unit': '%',
                'weight': 0.20,
                'max_points': 20.0,
                'data_source': 'manual',
                'order': 2,
            },
            {
                'name': 'Доля студентов в научных проектах',
                'description': 'Процент студентов, вовлечённых в научно-исследовательские проекты',
                'max_value': 100.0,
                'unit': '%',
                'weight': 0.40,
                'max_points': 40.0,
                'data_source': 'manual',
                'order': 3,
            },
        ])

        # === Группа 2: Привлечение внешних преподавателей (100 б.) ===
        g2, _ = KpiGroup.objects.get_or_create(
            name='Привлечение внешних преподавателей',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Привлечение преподавателей из индустрии и других вузов',
                'weight': 100.0 / 700.0,
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 2,
            }
        )
        self._create_indicators(g2, [
            {
                'name': 'Количество внешних преподавателей',
                'description': 'Привлечённые преподаватели из индустрии и других вузов',
                'max_value': 10.0,
                'unit': 'чел.',
                'weight': 1.0,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 1,
            },
        ])

        # === Группа 3: Научно-методическая деятельность (100 б.) ===
        g3, _ = KpiGroup.objects.get_or_create(
            name='Научно-методическая деятельность',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Публикации, конференции, учебные материалы',
                'weight': 100.0 / 700.0,
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 3,
            }
        )
        self._create_indicators(g3, [
            {
                'name': 'Публикации в рецензируемых журналах',
                'description': 'Статьи в рецензируемых научных журналах',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 0.30,
                'max_points': 30.0,
                'data_source': 'api',
                'order': 1,
            },
            {
                'name': 'Материалы конференций CORE A*/A',
                'description': 'Публикации в трудах конференций уровня CORE A*/A',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 0.30,
                'max_points': 30.0,
                'data_source': 'api',
                'order': 2,
            },
            {
                'name': 'Организованные конференции',
                'description': 'Конференции, организованные при участии руководителя',
                'max_value': 5.0,
                'unit': 'шт.',
                'weight': 0.20,
                'max_points': 20.0,
                'data_source': 'manual',
                'order': 3,
            },
            {
                'name': 'Разработанные учебные материалы',
                'description': 'Подготовленные учебные пособия, курсы, материалы',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 0.20,
                'max_points': 20.0,
                'data_source': 'manual',
                'order': 4,
            },
        ])

        # === Группа 4: Взаимодействие с индустрией (100 б.) ===
        g4, _ = KpiGroup.objects.get_or_create(
            name='Взаимодействие с индустрией',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Мероприятия, хакатоны, привлечение финансирования',
                'weight': 100.0 / 700.0,
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 4,
            }
        )
        self._create_indicators(g4, [
            {
                'name': 'Мероприятия и хакатоны',
                'description': 'Организованные мероприятия, хакатоны, воркшопы с индустрией',
                'max_value': 10.0,
                'unit': 'шт.',
                'weight': 0.40,
                'max_points': 40.0,
                'data_source': 'manual',
                'order': 1,
            },
            {
                'name': 'Привлечённое финансирование',
                'description': 'Объём привлечённого внешнего финансирования',
                'max_value': 5000000.0,
                'unit': '₽',
                'weight': 0.60,
                'max_points': 60.0,
                'data_source': 'manual',
                'order': 2,
            },
        ])

        # === Группа 5: Управление программой (200 б.) ===
        g5, _ = KpiGroup.objects.get_or_create(
            name='Управление программой',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Своевременная отчётность и выполнение KPI грантов',
                'weight': 200.0 / 700.0,
                'max_points': 200.0,
                'min_threshold': 100.0,
                'order': 5,
            }
        )
        self._create_indicators(g5, [
            {
                'name': 'Своевременность отчётности',
                'description': 'Процент отчётов, сданных в срок',
                'max_value': 100.0,
                'unit': '%',
                'weight': 0.50,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 1,
            },
            {
                'name': 'Выполнение KPI грантов',
                'description': 'Процент выполнения показателей по грантам и проектам',
                'max_value': 100.0,
                'unit': '%',
                'weight': 0.50,
                'max_points': 100.0,
                'data_source': 'manual',
                'order': 2,
            },
        ])

        # === Группа 6: Удовлетворённость (100 б.) ===
        g6, _ = KpiGroup.objects.get_or_create(
            name='Удовлетворённость',
            role=KpiGroup.ROLE_ROP,
            defaults={
                'description': 'Оценки удовлетворённости студентов и партнёров',
                'weight': 100.0 / 700.0,
                'max_points': 100.0,
                'min_threshold': 50.0,
                'order': 6,
            }
        )
        self._create_indicators(g6, [
            {
                'name': 'Удовлетворённость студентов',
                'description': 'Средняя оценка удовлетворённости студентов (шкала 1-5)',
                'max_value': 5.0,
                'unit': 'балл',
                'weight': 0.60,
                'max_points': 60.0,
                'data_source': 'manual',
                'order': 1,
            },
            {
                'name': 'Удовлетворённость партнёров',
                'description': 'Средняя оценка удовлетворённости индустриальных партнёров (шкала 1-5)',
                'max_value': 5.0,
                'unit': 'балл',
                'weight': 0.40,
                'max_points': 40.0,
                'data_source': 'manual',
                'order': 2,
            },
        ])

        self.stdout.write(self.style.SUCCESS(
            '[OK] РОП: 6 групп, 14 показателей, итого 700 баллов'
        ))

    def _create_indicators(self, group, indicators_data):
        """Создание показателей для группы."""
        for ind_data in indicators_data:
            KpiIndicator.objects.get_or_create(
                group=group,
                name=ind_data['name'],
                defaults=ind_data
            )
