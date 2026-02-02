# backend/apps/kpi/services/kpi_calculator.py

from django.db.models import Sum, Avg, Count, Q, F
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation

User = get_user_model()
logger = logging.getLogger(__name__)


class KpiCalculator:
    """
    Сервис для расчета ключевых показателей эффективности (KPI).

    Основные функции:
    - Расчет итогового балла KPI для пользователя за период
    - Генерация данных для дашборда
    - Создание персонализированных рекомендаций
    - Расчет премиальных выплат
    """

    # Пороговые значения для определения уровня эффективности
    PERFORMANCE_THRESHOLDS = {
        'высокий': 90.0,  # >= 90% - высокая эффективность
        'средний': 70.0,  # >= 70% - средняя эффективность
        'низкий': 0.0  # < 70% - низкая эффективность
    }

    # Коэффициенты премиальных выплат (% от базовой ставки)
    BONUS_COEFFICIENTS = {
        'высокий': 0.50,  # 50% премия
        'средний': 0.25,  # 25% премия
        'низкий': 0.00  # Без премии
    }

    # Базовая месячная ставка для расчета премии (в рублях)
    BASE_SALARY = 50000.0

    def calculate_total_score(self, user_id: int, period: str) -> Dict:
        """
        Расчет итогового балла KPI для пользователя за период.

        Args:
            user_id: ID пользователя
            period: Период в формате 'YYYY-MM'

        Returns:
            Dict с полями:
                - total_score: Итоговый балл (0-100)
                - performance_level: Уровень эффективности
                - bonus_amount: Сумма премии
                - group_scores: Баллы по группам показателей
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return self._empty_result()

        # Получаем все группы KPI
        kpi_groups = KpiGroup.objects.all().order_by('order')

        if not kpi_groups.exists():
            logger.warning("Не найдены группы KPI в системе")
            return self._empty_result()

        # Расчет баллов по каждой группе
        group_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0

        for group in kpi_groups:
            group_result = self._calculate_group_score(user_id, group, period)
            group_scores[group.id] = group_result

            # Взвешенный вклад группы в общий балл
            total_weighted_score += group_result['score'] * group.weight
            total_weight += group.weight

        # Итоговый балл (средневзвешенный)
        total_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Определение уровня эффективности
        performance_level = self._determine_performance_level(total_score)

        # Расчет премии
        bonus_amount = self._calculate_bonus(total_score)

        return {
            'total_score': round(total_score, 2),
            'performance_level': performance_level,
            'bonus_amount': bonus_amount,
            'group_scores': group_scores
        }

    def _calculate_group_score(self, user_id: int, group: KpiGroup, period: str) -> Dict:
        """
        Расчет балла для группы показателей.

        Args:
            user_id: ID пользователя
            group: Объект группы KPI
            period: Период в формате 'YYYY-MM'

        Returns:
            Dict с данными группы и её показателей
        """
        indicators = group.indicators.all().order_by('order')

        if not indicators.exists():
            return {
                'name': group.name,
                'score': 0.0,
                'indicators': []
            }

        indicator_results = []
        total_weighted_completion = 0.0
        total_indicator_weight = 0.0

        for indicator in indicators:
            indicator_data = self._calculate_indicator_completion(
                user_id, indicator, period
            )
            indicator_results.append(indicator_data)

            # Взвешенный вклад показателя в балл группы
            completion = indicator_data['completion_percent']
            total_weighted_completion += completion * indicator.weight
            total_indicator_weight += indicator.weight

        # Средневзвешенный балл группы
        group_score = (
            total_weighted_completion / total_indicator_weight
            if total_indicator_weight > 0 else 0.0
        )

        return {
            'name': group.name,
            'score': round(group_score, 2),
            'indicators': indicator_results
        }

    def _calculate_indicator_completion(
            self,
            user_id: int,
            indicator: KpiIndicator,
            period: str
    ) -> Dict:
        """
        Расчет процента выполнения для отдельного показателя.

        Args:
            user_id: ID пользователя
            indicator: Объект показателя KPI
            period: Период в формате 'YYYY-MM'

        Returns:
            Dict с данными показателя
        """
        try:
            kpi_value = KpiValue.objects.get(
                user_id=user_id,
                indicator=indicator,
                period=period,
                status=KpiValue.STATUS_APPROVED
            )
            actual_value = float(kpi_value.actual_value)
            target_value = float(kpi_value.target_value)
        except KpiValue.DoesNotExist:
            # Если нет данных за период, считаем 0
            actual_value = 0.0
            target_value = float(indicator.max_value) if indicator.max_value > 0 else 1.0

        # Процент выполнения (с ограничением максимум 100%)
        if target_value > 0:
            completion_percent = min((actual_value / target_value) * 100, 100.0)
        else:
            completion_percent = 0.0

        return {
            'id': indicator.id,
            'name': indicator.name,
            'actual_value': actual_value,
            'target_value': target_value,
            'completion_percent': round(completion_percent, 2),
            'unit': indicator.unit,
            'weight': indicator.weight
        }

    def _determine_performance_level(self, total_score: float) -> str:
        """
        Определение уровня эффективности на основе итогового балла.

        Args:
            total_score: Итоговый балл (0-100)

        Returns:
            Уровень эффективности: 'высокий', 'средний' или 'низкий'
        """
        if total_score >= self.PERFORMANCE_THRESHOLDS['высокий']:
            return 'высокий'
        elif total_score >= self.PERFORMANCE_THRESHOLDS['средний']:
            return 'средний'
        else:
            return 'низкий'

    def _calculate_bonus(self, total_score: float) -> float:
        """
        Расчет премиальной выплаты на основе итогового балла KPI.

        Args:
            total_score: Итоговый балл (0-100)

        Returns:
            Сумма премии в рублях
        """
        performance_level = self._determine_performance_level(total_score)
        bonus_coefficient = self.BONUS_COEFFICIENTS[performance_level]

        # Премия = базовая ставка * коэффициент
        bonus_amount = self.BASE_SALARY * bonus_coefficient

        return round(bonus_amount, 2)

    def calculate_dashboard(self, user_id: int, period: str) -> Dict:
        """
        Генерация полных данных для дашборда пользователя.

        Args:
            user_id: ID пользователя
            period: Период в формате 'YYYY-MM'

        Returns:
            Dict со всеми данными для отображения на дашборде
        """
        # Основные расчеты
        result = self.calculate_total_score(user_id, period)

        # Преобразуем данные для фронтенда
        dashboard_data = {
            'total_score': result['total_score'],
            'performance_level': result['performance_level'],
            'bonus_amount': result['bonus_amount'],
            'group_scores': result['group_scores'],
            'period': period
        }

        return dashboard_data

    def generate_recommendations(self, user_id: int, period: str) -> List[Dict]:
        """
        Генерация персонализированных рекомендаций для улучшения KPI.

        Рекомендации создаются для показателей с выполнением < 70%.

        Args:
            user_id: ID пользователя
            period: Период в формате 'YYYY-MM'

        Returns:
            List рекомендаций
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return []

        # Получаем все показатели с низким выполнением
        kpi_values = KpiValue.objects.filter(
            user_id=user_id,
            period=period,
            status=KpiValue.STATUS_APPROVED
        ).select_related('indicator', 'indicator__group')

        recommendations = []

        for kpi_value in kpi_values:
            # Рассчитываем процент выполнения
            if kpi_value.target_value > 0:
                completion = (kpi_value.actual_value / kpi_value.target_value) * 100
            else:
                completion = 0.0

            # Генерируем рекомендацию для показателей < 70%
            if completion < 70.0:
                recommendation_text = self._generate_recommendation_text(
                    kpi_value.indicator,
                    completion,
                    kpi_value.actual_value,
                    kpi_value.target_value
                )

                # Целевое значение для следующего периода
                target_improvement = kpi_value.target_value * 0.8  # 80% от плана

                # Вычисляем дедлайн (следующий месяц)
                deadline_period = self._get_next_period(period)

                # Создаем или обновляем рекомендацию в БД
                recommendation, created = KpiRecommendation.objects.update_or_create(
                    user=user,
                    indicator=kpi_value.indicator,
                    period=period,
                    defaults={
                        'text': recommendation_text,
                        'target_value': target_improvement,
                        'deadline_period': deadline_period,
                        'is_completed': False
                    }
                )

                recommendations.append({
                    'id': recommendation.id,
                    'indicator_name': kpi_value.indicator.name,
                    'text': recommendation_text,
                    'target_value': round(target_improvement, 1),
                    'deadline_period': deadline_period,
                    'current_completion': round(completion, 1)
                })

        return recommendations

    def _generate_recommendation_text(
            self,
            indicator: KpiIndicator,
            completion: float,
            actual: float,
            target: float
    ) -> str:
        """
        Генерация текста рекомендации на основе показателя.

        Args:
            indicator: Объект показателя KPI
            completion: Процент выполнения
            actual: Фактическое значение
            target: Целевое значение

        Returns:
            Текст рекомендации
        """
        gap = target - actual

        # Шаблоны рекомендаций в зависимости от типа показателя
        recommendations_templates = {
            'публикации': f"Для достижения целевого показателя необходимо опубликовать ещё {gap:.0f} статей. "
                          f"Рекомендуется подготовить материалы для конференций уровня ВАК или Scopus.",

            'гранты': f"Текущий уровень выполнения {completion:.1f}%. "
                      f"Рекомендуется подать заявки на участие в {int(gap)} грантовых конкурсах. "
                      f"Обратите внимание на конкурсы РНФ, РФФИ и внутренние гранты университета.",

            'проекты': f"Необходимо завершить или инициировать {gap:.0f} проектов. "
                       f"Рассмотрите возможность участия в прикладных НИР или совместных проектах с индустрией.",

            'цитирования': f"Для улучшения индекса цитирования ({completion:.1f}% от цели) рекомендуется: "
                           f"продвижение публикаций в научных сетях, участие в конференциях, "
                           f"налаживание сотрудничества с активными исследовательскими группами.",

            'студенты': f"Требуется увеличить работу со студентами на {gap:.0f} чел. "
                        f"Рекомендации: руководство курсовыми/дипломными работами, "
                        f"привлечение студентов к научным проектам.",

            'мероприятия': f"Необходимо принять участие ещё в {gap:.0f} мероприятиях. "
                           f"Рекомендуется участие в конференциях, семинарах, вебинарах по вашему направлению."
        }

        # Определяем тип показателя по ключевым словам
        indicator_name_lower = indicator.name.lower()

        for key, template in recommendations_templates.items():
            if key in indicator_name_lower:
                return template

        # Общая рекомендация, если тип не определен
        return (f"Текущий уровень выполнения показателя '{indicator.name}': {completion:.1f}%. "
                f"Для достижения цели необходимо увеличить значение на {gap:.1f} {indicator.unit}. "
                f"Рекомендуется проанализировать причины отставания и разработать план корректирующих действий.")

    def _get_next_period(self, current_period: str) -> str:
        """
        Вычисление следующего периода.

        Args:
            current_period: Текущий период 'YYYY-MM'

        Returns:
            Следующий период 'YYYY-MM'
        """
        year, month = map(int, current_period.split('-'))

        if month == 12:
            return f"{year + 1}-01"
        else:
            return f"{year}-{month + 1:02d}"

    def calculate_all_users_kpi(self, period: Optional[str] = None):
        """
        Массовый расчет KPI для всех активных пользователей.
        Используется в Celery задачах для автоматического расчета.

        Args:
            period: Период для расчета (если None, используется текущий месяц)
        """
        if period is None:
            period = datetime.now().strftime('%Y-%m')

        users = User.objects.filter(is_active=True, is_superuser=False)

        logger.info(f"Начало расчета KPI для {users.count()} пользователей за период {period}")

        success_count = 0
        error_count = 0

        for user in users:
            try:
                result = self.calculate_total_score(user.id, period)
                logger.debug(f"User {user.username}: KPI = {result['total_score']}")
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка расчета KPI для пользователя {user.username}: {str(e)}")
                error_count += 1

        logger.info(f"Расчет завершен. Успешно: {success_count}, Ошибок: {error_count}")

        return {
            'success_count': success_count,
            'error_count': error_count,
            'period': period
        }

    def _empty_result(self) -> Dict:
        """
        Возвращает пустой результат при ошибках.
        """
        return {
            'total_score': 0.0,
            'performance_level': 'низкий',
            'bonus_amount': 0.0,
            'group_scores': {}
        }

    def get_user_kpi_history(self, user_id: int, months: int = 6) -> List[Dict]:
        """
        Получение истории KPI пользователя за последние N месяцев.

        Args:
            user_id: ID пользователя
            months: Количество месяцев истории

        Returns:
            List с историческими данными KPI
        """
        history = []
        current_date = datetime.now()

        for i in range(months):
            # Вычисляем период
            period_date = current_date - timedelta(days=30 * i)
            period = period_date.strftime('%Y-%m')

            # Получаем данные за период
            result = self.calculate_total_score(user_id, period)

            history.append({
                'period': period,
                'total_score': result['total_score'],
                'performance_level': result['performance_level'],
                'bonus_amount': result['bonus_amount']
            })

        # Сортируем по возрастанию (от старых к новым)
        history.reverse()

        return history

    def get_top_performers(self, period: str, limit: int = 10) -> List[Dict]:
        """
        Получение списка лучших сотрудников за период.
        Используется для дашборда руководителя.

        Args:
            period: Период в формате 'YYYY-MM'
            limit: Максимальное количество сотрудников в списке

        Returns:
            List лучших сотрудников с их KPI
        """
        users = User.objects.filter(is_active=True, is_superuser=False)

        performers = []

        for user in users:
            result = self.calculate_total_score(user.id, period)

            performers.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'total_score': result['total_score'],
                'performance_level': result['performance_level'],
                'bonus_amount': result['bonus_amount']
            })

        # Сортируем по убыванию балла
        performers.sort(key=lambda x: x['total_score'], reverse=True)

        return performers[:limit]