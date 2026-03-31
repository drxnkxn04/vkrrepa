# backend/apps/kpi/services/kpi_calculator.py

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Avg, Count, Q, F
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation, UserProfile, get_user_kpi_role

User = get_user_model()
logger = logging.getLogger(__name__)


class KpiCalculator:
    """
    Сервис для расчета KPI.

    Поддерживает две роли:
    - ППС (преподаватель): 5 групп, 500 баллов макс.
    - РОП (руководитель): 6 групп, 700 баллов макс.

    Бонусные коэффициенты (из Excel):
    - Высокий уровень (≥90%): +15%
    - Средний уровень (70-89%): 0%
    - Низкий уровень (<70%): -50%
    """

    PERFORMANCE_THRESHOLDS = {
        'высокий': 90.0,
        'средний': 70.0,
        'низкий': 0.0,
    }

    BONUS_COEFFICIENTS = {
        'высокий': 0.15,
        'средний': 0.00,
        'низкий': 0.00,
    }

    BASE_SALARY = getattr(settings, 'KPI_BASE_SALARY', 50000.0)
    CACHE_TTL = getattr(settings, 'KPI_CACHE_TTL', 300)

    @staticmethod
    def _cache_key(prefix: str, user_id: int, period: str) -> str:
        return f'kpi:{prefix}:{user_id}:{period}'

    @staticmethod
    def invalidate_cache(user_id: int, period: str):
        """Сброс кэша для пользователя и периода."""
        cache.delete(KpiCalculator._cache_key('score', user_id, period))
        cache.delete(KpiCalculator._cache_key('dashboard', user_id, period))

    def _get_user_role(self, user) -> str:
        """Определяет роль пользователя (pps или rop)."""
        return get_user_kpi_role(user)

    def _get_groups_for_user(self, user) -> 'QuerySet':
        """Возвращает группы KPI для роли пользователя."""
        role = self._get_user_role(user)
        groups = KpiGroup.objects.filter(role=role).order_by('order')
        if not groups.exists():
            # Fallback: все группы без фильтра по роли
            groups = KpiGroup.objects.all().order_by('order')
        return groups

    def calculate_total_score(self, user_id: int, period: str) -> Dict:
        """
        Расчет итогового балла KPI для пользователя за период.

        Returns:
            Dict: total_score (0-100), total_points, max_points,
                  performance_level, bonus_amount, group_scores
        """
        cache_key = self._cache_key('score', user_id, period)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return self._empty_result()

        kpi_groups = self._get_groups_for_user(user)

        if not kpi_groups.exists():
            logger.warning("Не найдены группы KPI в системе")
            return self._empty_result()

        group_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        total_points = 0.0
        max_points = 0.0

        for group in kpi_groups:
            group_result = self._calculate_group_score(user_id, group, period)
            group_scores[group.id] = group_result

            total_weighted_score += group_result['score'] * group.weight
            total_weight += group.weight
            total_points += group_result['points']
            max_points += group.max_points

        # Итоговый процент
        total_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        performance_level = self._determine_performance_level(total_score)
        bonus_amount = self._calculate_bonus(total_score)

        # Проверка минимальных порогов
        threshold_warnings = self._check_thresholds(group_scores, kpi_groups)

        result = {
            'total_score': round(total_score, 2),
            'total_points': round(total_points, 1),
            'max_points': round(max_points, 1),
            'performance_level': performance_level,
            'bonus_amount': bonus_amount,
            'group_scores': group_scores,
            'threshold_warnings': threshold_warnings,
            'user_role': self._get_user_role(user),
        }

        cache.set(cache_key, result, self.CACHE_TTL)
        return result

    def _calculate_group_score(self, user_id: int, group: KpiGroup, period: str) -> Dict:
        """Расчет балла для группы показателей."""
        indicators = group.indicators.all().order_by('order')

        if not indicators.exists():
            return {
                'name': group.name,
                'score': 0.0,
                'points': 0.0,
                'max_points': group.max_points,
                'min_threshold': group.min_threshold,
                'indicators': [],
            }

        indicator_results = []
        total_weighted_completion = 0.0
        total_indicator_weight = 0.0
        group_points = 0.0

        for indicator in indicators:
            indicator_data = self._calculate_indicator_completion(
                user_id, indicator, period
            )
            indicator_results.append(indicator_data)

            completion = indicator_data['completion_percent']
            total_weighted_completion += completion * indicator.weight
            total_indicator_weight += indicator.weight

            # Баллы = max_points * (completion / 100)
            indicator_points = indicator.max_points * (completion / 100.0)
            group_points += indicator_points

        group_score = (
            total_weighted_completion / total_indicator_weight
            if total_indicator_weight > 0 else 0.0
        )

        return {
            'name': group.name,
            'score': round(group_score, 2),
            'points': round(group_points, 1),
            'max_points': group.max_points,
            'min_threshold': group.min_threshold,
            'indicators': indicator_results,
        }

    def _calculate_indicator_completion(
            self,
            user_id: int,
            indicator: KpiIndicator,
            period: str
    ) -> Dict:
        """Расчет процента выполнения для отдельного показателя."""
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
            actual_value = 0.0
            target_value = float(indicator.max_value) if indicator.max_value > 0 else 1.0

        if target_value > 0:
            completion_percent = min((actual_value / target_value) * 100, 100.0)
        elif actual_value > 0:
            completion_percent = 100.0
        else:
            completion_percent = 0.0

        return {
            'id': indicator.id,
            'name': indicator.name,
            'actual_value': actual_value,
            'target_value': target_value,
            'completion_percent': round(completion_percent, 2),
            'unit': indicator.unit,
            'weight': indicator.weight,
            'max_points': indicator.max_points,
            'points': round(indicator.max_points * (completion_percent / 100.0), 1),
        }

    def _check_thresholds(self, group_scores: Dict, kpi_groups) -> List[Dict]:
        """Проверка минимальных порогов по группам.

        Показывает предупреждение только если:
        - У пользователя есть хоть какие-то баллы (не пустой период)
        - Дефицит больше 10% от порога (игнорирует мелкие отклонения)
        """
        # Если у пользователя вообще нет данных — не показываем предупреждения
        total_points = sum(gs['points'] for gs in group_scores.values())
        if total_points == 0:
            return []

        warnings = []
        for group in kpi_groups:
            gs = group_scores.get(group.id)
            if gs and group.min_threshold > 0:
                deficit = group.min_threshold - gs['points']
                # Показываем только если дефицит > 10% от порога
                if deficit > group.min_threshold * 0.10:
                    warnings.append({
                        'group_name': group.name,
                        'current_points': gs['points'],
                        'min_threshold': group.min_threshold,
                        'deficit': round(deficit, 1),
                    })
        return warnings

    def _determine_performance_level(self, total_score: float) -> str:
        if total_score >= self.PERFORMANCE_THRESHOLDS['высокий']:
            return 'высокий'
        elif total_score >= self.PERFORMANCE_THRESHOLDS['средний']:
            return 'средний'
        else:
            return 'низкий'

    def _calculate_bonus(self, total_score: float) -> float:
        """
        Расчет премиальной выплаты.
        +15% при высоком, 0% при среднем и низком.
        """
        performance_level = self._determine_performance_level(total_score)
        bonus_coefficient = self.BONUS_COEFFICIENTS[performance_level]
        return max(round(self.BASE_SALARY * bonus_coefficient, 2), 0.0)

    def calculate_dashboard(self, user_id: int, period: str) -> Dict:
        """Генерация полных данных для дашборда пользователя."""
        cache_key = self._cache_key('dashboard', user_id, period)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = self.calculate_total_score(user_id, period)

        dashboard_data = {
            'total_score': result['total_score'],
            'total_points': result['total_points'],
            'max_points': result['max_points'],
            'performance_level': result['performance_level'],
            'bonus_amount': result['bonus_amount'],
            'group_scores': result['group_scores'],
            'threshold_warnings': result['threshold_warnings'],
            'user_role': result['user_role'],
            'period': period,
        }

        cache.set(cache_key, dashboard_data, self.CACHE_TTL)
        return dashboard_data

    def generate_recommendations(self, user_id: int, period: str) -> List[Dict]:
        """
        Генерация персонализированных рекомендаций для улучшения KPI.
        Рекомендации для показателей с выполнением < 80%.
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return []

        kpi_values = KpiValue.objects.filter(
            user_id=user_id,
            period=period,
            status=KpiValue.STATUS_APPROVED
        ).select_related('indicator', 'indicator__group')

        recommendations = []

        for kpi_value in kpi_values:
            if kpi_value.target_value <= 0:
                continue

            completion = min((kpi_value.actual_value / kpi_value.target_value) * 100, 100.0)

            if completion >= 80.0:
                continue

            if completion < 30.0:
                priority = KpiRecommendation.PRIORITY_HIGH
            elif completion < 60.0:
                priority = KpiRecommendation.PRIORITY_MEDIUM
            else:
                priority = KpiRecommendation.PRIORITY_LOW

            recommendation_text = self._generate_recommendation_text(
                kpi_value.indicator,
                completion,
                kpi_value.actual_value,
                kpi_value.target_value
            )

            deadline_period = self._get_next_period(period)

            defaults = {
                'text': recommendation_text,
                'priority': priority,
                'actual_value': kpi_value.actual_value,
                'target_value': kpi_value.target_value,
                'current_completion': round(completion, 1),
                'deadline_period': deadline_period,
            }

            recommendation, created = KpiRecommendation.objects.update_or_create(
                user=user,
                indicator=kpi_value.indicator,
                period=period,
                defaults=defaults
            )

            recommendations.append({
                'id': recommendation.id,
                'indicator_name': kpi_value.indicator.name,
                'indicator_group': kpi_value.indicator.group.name if kpi_value.indicator.group else '',
                'indicator_unit': kpi_value.indicator.unit or '',
                'text': recommendation_text,
                'priority': priority,
                'actual_value': round(kpi_value.actual_value, 1),
                'target_value': round(kpi_value.target_value, 1),
                'current_completion': round(completion, 1),
                'deadline_period': deadline_period,
                'is_completed': recommendation.is_completed,
            })

        priority_order = {
            KpiRecommendation.PRIORITY_HIGH: 0,
            KpiRecommendation.PRIORITY_MEDIUM: 1,
            KpiRecommendation.PRIORITY_LOW: 2,
        }
        recommendations.sort(key=lambda r: (priority_order.get(r['priority'], 9), r['current_completion']))

        return recommendations

    def _generate_recommendation_text(
            self,
            indicator: KpiIndicator,
            completion: float,
            actual: float,
            target: float
    ) -> str:
        """Генерация текста рекомендации на основе показателя."""
        gap = max(target - actual, 0)
        unit = indicator.unit or 'ед.'

        if completion < 30:
            urgency = "Критически низкий уровень выполнения."
        elif completion < 60:
            urgency = "Показатель значительно ниже плана."
        else:
            urgency = "Показатель близок к плановому, но ещё не достигнут."

        indicator_name_lower = indicator.name.lower()

        templates = {
            'публикац': (
                f"{urgency} Текущий результат: {actual:.0f} из {target:.0f} {unit}. "
                f"Необходимо опубликовать ещё {gap:.0f} статей. "
                f"Действия: подготовить рукописи для журналов ВАК/Scopus, "
                f"оформить результаты конференций в статьи, рассмотреть соавторство."
            ),
            'конференц': (
                f"{urgency} Участие: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: подать тезисы на ближайшие конференции, "
                f"рассмотреть участие в онлайн-конференциях, "
                f"выступить с докладом на внутренних семинарах."
            ),
            'core': (
                f"{urgency} Опубликовано {actual:.0f} из {target:.0f} материалов CORE A*/A. "
                f"Действия: подать статьи на ведущие конференции, "
                f"подготовить рукописи совместно с международными коллегами."
            ),
            'грант': (
                f"{urgency} Текущий результат: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: подать заявки на конкурсы РНФ, внутренние гранты, "
                f"рассмотреть международные программы и совместные заявки."
            ),
            'ниокр': (
                f"{urgency} Текущий результат: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: инициировать новые НИР, подать заявки на гранты, "
                f"рассмотреть хоздоговорные работы с индустриальными партнёрами."
            ),
            'проект': (
                f"{urgency} Текущий результат: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: завершить текущие этапы проектов, инициировать новые, "
                f"рассмотреть проекты с индустриальными партнёрами."
            ),
            'доклад': (
                f"{urgency} Докладов: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: подать тезисы на международные конференции, "
                f"организовать секцию или круглый стол, выступить на семинарах."
            ),
            'мероприят': (
                f"{urgency} Проведено: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: организовать хакатон или воркшоп, "
                f"привлечь индустриальных партнёров к совместным мероприятиям."
            ),
            'хакатон': (
                f"{urgency} Проведено: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: организовать хакатон с индустриальными партнёрами, "
                f"привлечь спонсоров и менторов из компаний."
            ),
            'студент': (
                f"{urgency} Текущий результат: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: привлечь студентов к научным проектам, "
                f"организовать научный кружок, предложить темы курсовых и дипломных."
            ),
            'удовлетвор': (
                f"{urgency} Текущая оценка: {actual:.1f} из {target:.1f} {unit}. "
                f"Действия: провести опрос для выявления проблемных зон, "
                f"внедрить обратную связь по курсам, улучшить коммуникацию."
            ),
            'отчётност': (
                f"{urgency} Своевременность: {actual:.0f}% из {target:.0f}%. "
                f"Действия: внедрить календарный план отчётности, "
                f"настроить напоминания о дедлайнах."
            ),
            'финансиров': (
                f"{urgency} Привлечено: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: подготовить заявки на гранты, "
                f"обратиться к индустриальным партнёрам за спонсорством."
            ),
            'материал': (
                f"{urgency} Разработано: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: подготовить новые РПД и учебные пособия, "
                f"обновить существующие материалы, привлечь коллег к разработке."
            ),
            'нагрузк': (
                f"{urgency} Текущая нагрузка: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: взять дополнительные курсы, "
                f"рассмотреть межкафедральное преподавание."
            ),
            'кредит': (
                f"{urgency} Текущая нагрузка: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: взять дополнительные курсы, "
                f"рассмотреть преподавание на смежных программах."
            ),
            'аттестац': (
                f"{urgency} Доля: {actual:.0f}% из {target:.0f}%. "
                f"Действия: усилить контроль успеваемости, "
                f"организовать дополнительные консультации для отстающих студентов."
            ),
            'практическ': (
                f"{urgency} Доля: {actual:.0f}% из {target:.0f}%. "
                f"Действия: увеличить количество лабораторных и практических занятий, "
                f"внедрить проектное обучение."
            ),
            'преподават': (
                f"{urgency} Привлечено: {actual:.0f} из {target:.0f} {unit}. "
                f"Действия: обратиться к партнёрам из индустрии, "
                f"пригласить специалистов для гостевых лекций."
            ),
        }

        for key, template in templates.items():
            if key in indicator_name_lower:
                return template

        return (
            f"{urgency} Текущий результат: {actual:.1f} из {target:.1f} {unit} "
            f"(выполнение {completion:.0f}%). "
            f"Необходимо увеличить значение на {gap:.1f} {unit}. "
            f"Проанализируйте причины отставания и составьте план действий на следующий месяц."
        )

    def _get_next_period(self, current_period: str) -> str:
        try:
            year, month = map(int, current_period.split('-'))
        except (ValueError, AttributeError):
            logger.exception(f"Некорректный формат периода: {current_period!r}")
            now = datetime.now()
            year, month = now.year, now.month
        if month == 12:
            return f"{year + 1}-01"
        else:
            return f"{year}-{month + 1:02d}"

    def calculate_all_users_kpi(self, period: Optional[str] = None):
        """Массовый расчет KPI для всех активных пользователей."""
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
            'period': period,
        }

    def _empty_result(self) -> Dict:
        return {
            'total_score': 0.0,
            'total_points': 0.0,
            'max_points': 0.0,
            'performance_level': 'низкий',
            'bonus_amount': 0.0,
            'group_scores': {},
            'threshold_warnings': [],
            'user_role': 'pps',
        }

    def get_user_kpi_history(self, user_id: int, months: int = 6) -> List[Dict]:
        """Получение истории KPI пользователя за последние N месяцев."""
        history = []
        now = datetime.now()
        year = now.year
        month = now.month

        for i in range(months):
            m = month - i
            y = year
            while m <= 0:
                m += 12
                y -= 1
            period = f"{y}-{m:02d}"

            try:
                result = self.calculate_total_score(user_id, period)
            except Exception:
                logger.exception(f"Ошибка расчёта KPI для user_id={user_id}, период={period}")
                result = self._empty_result()

            group_summary = {}
            for gid, gdata in result.get('group_scores', {}).items():
                group_summary[gdata['name']] = round(gdata['score'], 1)

            history.append({
                'period': period,
                'total_score': result['total_score'],
                'total_points': result.get('total_points', 0),
                'max_points': result.get('max_points', 0),
                'performance_level': result['performance_level'],
                'bonus_amount': result['bonus_amount'],
                'group_scores': group_summary,
            })

        history.reverse()
        return history

    def get_top_performers(self, period: str, limit: int = 10) -> List[Dict]:
        """Получение списка лучших сотрудников за период."""
        users = User.objects.filter(is_active=True, is_superuser=False)

        performers = []

        for user in users:
            try:
                result = self.calculate_total_score(user.id, period)
            except Exception:
                logger.exception(f"Ошибка расчёта KPI для user_id={user.id}, период={period}")
                continue

            performers.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'total_score': result['total_score'],
                'total_points': result.get('total_points', 0),
                'max_points': result.get('max_points', 0),
                'performance_level': result['performance_level'],
                'bonus_amount': result['bonus_amount'],
                'user_role': result.get('user_role', 'pps'),
            })

        performers.sort(key=lambda x: x['total_score'], reverse=True)

        return performers[:limit]
