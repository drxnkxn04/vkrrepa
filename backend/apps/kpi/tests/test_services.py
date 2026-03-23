# backend/apps/kpi/tests/test_services.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation
from ..services import KpiCalculator

User = get_user_model()


class KpiCalculatorTestCase(TestCase):
    """Тесты для KpiCalculator."""

    def setUp(self):
        """Подготовка тестовых данных."""
        # Создание тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Создание групп KPI
        self.group1 = KpiGroup.objects.create(
            name='Публикации',
            description='Публикационная активность',
            weight=0.5,  # 50% от общего балла
            order=1
        )

        self.group2 = KpiGroup.objects.create(
            name='Проекты',
            description='Участие в проектах',
            weight=0.3,  # 30% от общего балла
            order=2
        )

        self.group3 = KpiGroup.objects.create(
            name='Преподавание',
            description='Педагогическая работа',
            weight=0.2,  # 20% от общего балла
            order=3
        )

        # Создание показателей для группы "Публикации"
        self.indicator1 = KpiIndicator.objects.create(
            group=self.group1,
            name='Статьи Scopus',
            description='Публикации в журналах Scopus',
            max_value=10.0,
            unit='шт.',
            weight=2.0,
            data_source='manual',
            order=1
        )

        self.indicator2 = KpiIndicator.objects.create(
            group=self.group1,
            name='Конференции ВАК',
            description='Участие в конференциях ВАК',
            max_value=5.0,
            unit='шт.',
            weight=1.0,
            data_source='manual',
            order=2
        )

        # Создание показателей для группы "Проекты"
        self.indicator3 = KpiIndicator.objects.create(
            group=self.group2,
            name='Гранты',
            description='Участие в грантах',
            max_value=3.0,
            unit='шт.',
            weight=1.5,
            data_source='manual',
            order=1
        )

        # Создание показателя для группы "Преподавание"
        self.indicator4 = KpiIndicator.objects.create(
            group=self.group3,
            name='Студенты',
            description='Количество студентов под руководством',
            max_value=20.0,
            unit='чел.',
            weight=1.0,
            data_source='manual',
            order=1
        )

        self.calculator = KpiCalculator()
        self.test_period = '2024-12'

    def test_calculate_total_score_no_data(self):
        """Тест расчета KPI при отсутствии данных."""
        result = self.calculator.calculate_total_score(self.user.id, self.test_period)

        self.assertEqual(result['total_score'], 0.0)
        self.assertEqual(result['performance_level'], 'низкий')
        self.assertEqual(result['bonus_amount'], 0.0)  # 0% при низком уровне

    def test_calculate_total_score_perfect(self):
        """Тест расчета KPI при 100% выполнении всех показателей."""
        # Создаем значения с полным выполнением
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator1,
            period=self.test_period,
            actual_value=10.0,
            target_value=10.0,
            is_verified=True
        )

        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator2,
            period=self.test_period,
            actual_value=5.0,
            target_value=5.0,
            is_verified=True
        )

        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator3,
            period=self.test_period,
            actual_value=3.0,
            target_value=3.0,
            is_verified=True
        )

        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator4,
            period=self.test_period,
            actual_value=20.0,
            target_value=20.0,
            is_verified=True
        )

        result = self.calculator.calculate_total_score(self.user.id, self.test_period)

        self.assertEqual(result['total_score'], 100.0)
        self.assertEqual(result['performance_level'], 'высокий')
        self.assertEqual(result['bonus_amount'], 7500.0)  # +15% при высоком уровне

    def test_calculate_total_score_partial(self):
        """Тест расчета KPI при частичном выполнении."""
        # Статьи Scopus: 5 из 10 = 50%
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator1,
            period=self.test_period,
            actual_value=5.0,
            target_value=10.0,
            is_verified=True
        )

        # Конференции ВАК: 4 из 5 = 80%
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator2,
            period=self.test_period,
            actual_value=4.0,
            target_value=5.0,
            is_verified=True
        )

        # Гранты: 3 из 3 = 100%
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator3,
            period=self.test_period,
            actual_value=3.0,
            target_value=3.0,
            is_verified=True
        )

        # Студенты: 15 из 20 = 75%
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator4,
            period=self.test_period,
            actual_value=15.0,
            target_value=20.0,
            is_verified=True
        )

        result = self.calculator.calculate_total_score(self.user.id, self.test_period)

        # Ожидаемый расчет:
        # Группа "Публикации" (вес 0.5):
        #   - Scopus: 50% * вес 2.0 = 100
        #   - ВАК: 80% * вес 1.0 = 80
        #   - Средневзвешенный балл группы: (100 + 80) / (2.0 + 1.0) = 60%
        # Группа "Проекты" (вес 0.3):
        #   - Гранты: 100% * вес 1.5 = 150 / 1.5 = 100%
        # Группа "Преподавание" (вес 0.2):
        #   - Студенты: 75% * вес 1.0 = 75%
        # Итого: 60*0.5 + 100*0.3 + 75*0.2 = 30 + 30 + 15 = 75%

        self.assertAlmostEqual(result['total_score'], 75.0, places=1)
        self.assertEqual(result['performance_level'], 'средний')
        self.assertEqual(result['bonus_amount'], 0.0)  # 0% при среднем уровне

    def test_performance_level_boundaries(self):
        """Тест граничных значений для уровней эффективности."""
        # Тест для "высокий" уровень (>= 90%)
        level_high = self.calculator._determine_performance_level(90.0)
        self.assertEqual(level_high, 'высокий')

        level_high_above = self.calculator._determine_performance_level(95.0)
        self.assertEqual(level_high_above, 'высокий')

        # Тест для "средний" уровень (70-89%)
        level_medium = self.calculator._determine_performance_level(70.0)
        self.assertEqual(level_medium, 'средний')

        level_medium_mid = self.calculator._determine_performance_level(80.0)
        self.assertEqual(level_medium_mid, 'средний')

        # Тест для "низкий" уровень (< 70%)
        level_low = self.calculator._determine_performance_level(69.9)
        self.assertEqual(level_low, 'низкий')

        level_low_very = self.calculator._determine_performance_level(30.0)
        self.assertEqual(level_low_very, 'низкий')

    def test_bonus_calculation(self):
        """Тест расчета премии (коэффициенты из Excel: +15%/-50%)."""
        # Высокий уровень - +15% премия
        bonus_high = self.calculator._calculate_bonus(95.0)
        self.assertEqual(bonus_high, 7500.0)  # 50000 * 0.15

        # Средний уровень - 0% (без изменений)
        bonus_medium = self.calculator._calculate_bonus(75.0)
        self.assertEqual(bonus_medium, 0.0)  # 50000 * 0.00

        # Низкий уровень - 0% (без премии)
        bonus_low = self.calculator._calculate_bonus(50.0)
        self.assertEqual(bonus_low, 0.0)

    def test_generate_recommendations_low_performance(self):
        """Тест генерации рекомендаций для показателей с низким выполнением."""
        # Создаем показатель с низким выполнением (< 70%)
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator1,
            period=self.test_period,
            actual_value=3.0,  # 30% от целевого значения
            target_value=10.0,
            is_verified=True
        )

        recommendations = self.calculator.generate_recommendations(
            self.user.id,
            self.test_period
        )

        # Должна быть создана минимум одна рекомендация
        self.assertGreater(len(recommendations), 0)

        # Проверка структуры рекомендации
        rec = recommendations[0]
        self.assertIn('indicator_name', rec)
        self.assertIn('text', rec)
        self.assertIn('target_value', rec)
        self.assertIn('deadline_period', rec)
        self.assertIn('current_completion', rec)

        # Текущее выполнение должно быть 30%
        self.assertAlmostEqual(rec['current_completion'], 30.0, places=1)

    def test_generate_recommendations_good_performance(self):
        """Тест отсутствия рекомендаций при хорошем выполнении."""
        # Создаем показатель с хорошим выполнением (>= 70%)
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator1,
            period=self.test_period,
            actual_value=8.0,  # 80% от целевого значения
            target_value=10.0,
            is_verified=True
        )

        recommendations = self.calculator.generate_recommendations(
            self.user.id,
            self.test_period
        )

        # Не должно быть рекомендаций для хорошо выполненных показателей
        self.assertEqual(len(recommendations), 0)

    def test_get_user_kpi_history(self):
        """Тест получения истории KPI."""
        # Создаем данные за несколько периодов
        periods = ['2024-10', '2024-11', '2024-12']

        for period in periods:
            KpiValue.objects.create(
                status=KpiValue.STATUS_APPROVED,
                user=self.user,
                indicator=self.indicator1,
                period=period,
                actual_value=5.0,
                target_value=10.0,
                is_verified=True
            )

        history = self.calculator.get_user_kpi_history(self.user.id, months=3)

        # Проверяем, что история содержит 3 записи
        self.assertEqual(len(history), 3)

        # Проверяем структуру записи истории
        for item in history:
            self.assertIn('period', item)
            self.assertIn('total_score', item)
            self.assertIn('performance_level', item)
            self.assertIn('bonus_amount', item)

    def test_indicator_completion_over_100(self):
        """Тест, что процент выполнения не превышает 100% при перевыполнении."""
        # Создаем показатель с перевыполнением
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user,
            indicator=self.indicator1,
            period=self.test_period,
            actual_value=15.0,  # 150% от целевого значения
            target_value=10.0,
            is_verified=True
        )

        indicator_data = self.calculator._calculate_indicator_completion(
            self.user.id,
            self.indicator1,
            self.test_period
        )

        # Процент выполнения должен быть ограничен 100%
        self.assertEqual(indicator_data['completion_percent'], 100.0)

    def test_get_next_period(self):
        """Тест вычисления следующего периода."""
        # Обычный случай
        next_period = self.calculator._get_next_period('2024-05')
        self.assertEqual(next_period, '2024-06')

        # Переход через год
        next_period_year = self.calculator._get_next_period('2024-12')
        self.assertEqual(next_period_year, '2025-01')


class KpiCalculatorIntegrationTestCase(TestCase):
    """Интеграционные тесты для KpiCalculator."""

    def setUp(self):
        """Подготовка тестовых данных."""
        # Создание двух пользователей
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )

        # Создание простой структуры KPI
        self.group = KpiGroup.objects.create(
            name='Тестовая группа',
            weight=1.0,
            order=1
        )

        self.indicator = KpiIndicator.objects.create(
            group=self.group,
            name='Тестовый показатель',
            max_value=10.0,
            unit='шт.',
            weight=1.0,
            data_source='manual',
            order=1
        )

        self.calculator = KpiCalculator()
        self.test_period = '2024-12'

    def test_calculate_all_users_kpi(self):
        """Тест массового расчета KPI для всех пользователей."""
        # Создаем данные для обоих пользователей
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user1,
            indicator=self.indicator,
            period=self.test_period,
            actual_value=8.0,
            target_value=10.0
        )

        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user2,
            indicator=self.indicator,
            period=self.test_period,
            actual_value=5.0,
            target_value=10.0
        )

        result = self.calculator.calculate_all_users_kpi(self.test_period)

        self.assertEqual(result['success_count'], 2)
        self.assertEqual(result['error_count'], 0)
        self.assertEqual(result['period'], self.test_period)

    def test_get_top_performers(self):
        """Тест получения списка лучших сотрудников."""
        # User1: 80% выполнение
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user1,
            indicator=self.indicator,
            period=self.test_period,
            actual_value=8.0,
            target_value=10.0
        )

        # User2: 50% выполнение
        KpiValue.objects.create(
            status=KpiValue.STATUS_APPROVED,
            user=self.user2,
            indicator=self.indicator,
            period=self.test_period,
            actual_value=5.0,
            target_value=10.0
        )

        top_performers = self.calculator.get_top_performers(self.test_period, limit=10)

        # Проверяем, что user1 на первом месте (выше балл)
        self.assertEqual(len(top_performers), 2)
        self.assertEqual(top_performers[0]['user_id'], self.user1.id)
        self.assertGreater(
            top_performers[0]['total_score'],
            top_performers[1]['total_score']
        )

# Запуск тестов:
# python manage.py test apps.kpi.tests.test_services